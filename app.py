import os
import datetime
import gradio as gr
from search import search
from rerank import rerank
from llm import get_llm
from ingest import ingest
from config import TOP_K_FINAL
from patient.tracker import save_log, get_all_logs, cross_reference
from patient.timeline import build_plot
from contradiction import format_contradictions

# Build the prompt for the language model, including the context and the user's question
def _build_prompt(context, query):
    return (
        f"[INST] You are a medical assistant specializing in pemphigus vulgaris. " 
        f"Answer ONLY using the provided PubMed/PMC context. "
        f"If the answer is not supported by the context, say 'This is not covered in the indexed literature.'\n\n"
        f"Context:\n{context}\n\nQuestion: {query} [/INST]"
    )

# Format the sources (chunks of documents) used to answer the question, for display in the UI
def _format_sources(docs):
    if not docs:
        return "*No sources.*"
    parts = []
    for i, doc in enumerate(docs, 1):
        fname = os.path.basename(doc["path"])
        snippet = doc["content"][:250].replace("\n", " ")

        # Hyperlink for PubMed/PMC files
        if fname.startswith("pmid_"):
            pmid = fname[5:].replace(".txt", "")
            label = f"[PMID {pmid}](https://pubmed.ncbi.nlm.nih.gov/{pmid}/)"
        elif fname.startswith("pmc_"):
            pmc_id = fname[4:].replace(".txt", "")
            label = f"[PMC{pmc_id}](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_id}/)"
        else:
            label = fname

        parts.append(f"**{i}. {label}**: chunk {doc['chunk_id']}\n> {snippet}…")
    return "\n\n---\n\n".join(parts)

# This function handles the main Q&A logic and streams the answer as it is generated
def stream_answer(query, history, top_k):
    # If the user did not type any question, prompt them to do so
    if not query.strip():
        yield history, "*Ask a question to see sources.*", ""
        return

    try:
        # Step 1: Find relevant document chunks using semantic search
        candidates = search(query)
        if not candidates:
            msg = "No relevant documents found. Run ingestion first."
            # Add the user's question and a message from the assistant to the chat history
            yield history + [{"role": "user", "content": query},
                             {"role": "assistant", "content": msg}], "*No sources.*", ""
            return
        
        # Step 2: Rerank the candidate chunks to find the most relevant ones
        top_docs = rerank(query, candidates, int(top_k))
        # Combine the top chunks into a single context string
        context = "\n\n".join([d["content"] for d in top_docs])
        # Build the prompt for the language model
        prompt = _build_prompt(context, query)

        # Step 3: Generate the answer using the local language model
        llm = get_llm()
        token_ids = llm.tokenize(prompt.encode())
        max_tokens = 300
        max_prompt_tokens = llm.n_ctx() - max_tokens - 10
        # If the prompt is too long, truncate it to fit the model's context window
        if len(token_ids) > max_prompt_tokens:
            token_ids = token_ids[:max_prompt_tokens]
            prompt = llm.detokenize(token_ids).decode("utf-8", errors="ignore")

        # Prepare the sources markdown for display
        sources_md = _format_sources(top_docs)
        # Prepare the contradictions markdown for display
        contradiction_md = format_contradictions(top_docs)
        # Add the user's question and an empty assistant message to the chat history
        history = history + [{"role": "user", "content": query},
                              {"role": "assistant", "content": ""}]
        partial = ""
        # Stream the answer token by token as it is generated
        for chunk in llm(prompt, max_tokens=max_tokens, temperature=0.7, stream=True):
            partial += chunk["choices"][0]["text"]
            history[-1] = {"role": "assistant", "content": partial}
            yield history, sources_md, contradiction_md

    # Handle the case where the model file is missing
    except FileNotFoundError as e:
        yield history + [{"role": "user", "content": query},
                         {"role": "assistant", "content": f"{e}"}], "", ""
    # Handle any other errors gracefully
    except Exception as e:
        yield history + [{"role": "user", "content": query},
                         {"role": "assistant", "content": f"Error: {e}"}], "", ""

# This function runs the ingestion process to index new documents
def run_ingest(folder):
    if not folder.strip():
        return "Please enter a folder path."
    if not os.path.isdir(folder):
        return f"Folder not found: {folder}"
    try:
        ingest(folder)
        return "Ingestion complete."
    except Exception as e:
        return f"{e}"

# Custom CSS
CSS = """
footer { display: none !important; }
.source-panel { background: #f4f6f9; border-radius: 10px; padding: 14px; }
"""
# Build the Gradio UI
with gr.Blocks() as demo:

    # Title and description
    gr.Markdown("*Pemphigus Vulgaris Literature Q&A: fully offline.*")

    with gr.Tabs():
        #-----Tab 1 - QA ------#
        with gr.Tab("Ask"):
            with gr.Row():

                # Left sidebar: settings and ingestion controls
                with gr.Column(scale=1, min_width=230):
                    gr.Markdown("### Settings")
                    top_k_slider = gr.Slider(
                        minimum=1, maximum=10, value=TOP_K_FINAL, step=1,
                        label="Sources to use (Top K)"
                    )
                    gr.Markdown("---")
                    gr.Markdown("### Ingest Documents")
                    folder_input = gr.Textbox(
                        label="Folder path", value="data", placeholder="data"
                    )
                    ingest_btn = gr.Button("Ingest", variant="secondary", size="sm")
                    ingest_status = gr.Textbox(label="Status", interactive=False, lines=2)
                    # When the ingest button is clicked, run the ingestion process
                    ingest_btn.click(fn=run_ingest, inputs=folder_input, outputs=ingest_status)

                # Main area: chat interface and sources display
                with gr.Column(scale=3):
                    # Chatbot displays the conversation history
                    chatbot = gr.Chatbot(
                        height=440,
                        show_label=False,
                    )
                    with gr.Row():
                        # Textbox for user to enter their question
                        query_input = gr.Textbox(
                            placeholder="e.g. What are the first-line treatments for pemphigus vulgaris?",
                            show_label=False, scale=5, container=False
                        )
                        # Button to submit the question
                        ask_btn = gr.Button("Ask ➤", variant="primary", scale=1)
                        # Button to clear the chat
                        clear_btn = gr.Button("Clear", variant="secondary", scale=1)
                    
                    gr.Markdown("### Sources Used")
                    sources_output = gr.Markdown(
                        value="*Sources will appear here after asking a question*",
                        elem_classes=["source-panel"]
                    )

                    # Section to display the sources used for the answer
                    gr.Markdown("### Contradictions in Sources")
                    contradiction_output = gr.Markdown(
                        value="*Contradictions will appear here after asking a question.*",
                        elem_classes=["source-panel"]
                    )
            
            # Event handlers for the UI
            ask_btn.click(
                fn=stream_answer,
                inputs=[query_input, chatbot, top_k_slider],
                outputs=[chatbot, sources_output, contradiction_output]
            )
            query_input.submit(
                fn=stream_answer,
                inputs=[query_input, chatbot, top_k_slider],
                outputs=[chatbot, sources_output, contradiction_output]
            )
            clear_btn.click(
                fn=lambda: ([], "*Sources will appear here after asking a question.*", "*No contradictions.*"),
                outputs=[chatbot, sources_output, contradiction_output]
            )

        # Tab 2 - Trigger
        with gr.Tab("Trigger Log"):
            gr.Markdown("### Log Today's Entry")
            with gr.Row():
                log_date  = gr.Textbox(
                    label="Date",
                    value=str(datetime.date.today())
                )
                log_score = gr.Slider(1, 10, value=1, step=1,
                                      label="Skin Score (1=clear, 10=severe flare)")
            log_foods = gr.Textbox(
                label="Foods eaten (comma-separated)",
                placeholder="onion, garlic, tomato sauce, bread"
            )
            log_activities = gr.Textbox(
                label="Activities / stress / medications",
                placeholder="gym, stressful meeting, started new medication"
            )
            log_notes = gr.Textbox(label="Free notes", lines=2)
            log_btn   = gr.Button("Save Entry", variant="primary")
            log_status = gr.Textbox(label="Status", interactive=False)

            gr.Markdown("---\n### Cross-Reference with Literature")
            xref_btn    = gr.Button("Find Papers for These Foods", variant="secondary")
            xref_output = gr.Markdown(
                value="*Click above to search literature for your logged foods.*",
                elem_classes=["source-panel"]
            )

            def _save_log(date, foods, activities, score, notes):
                try:
                    save_log(date, foods, activities, score, notes)
                    return f"Saved entry for {date}."
                except Exception as e:
                    return f"Error: {e}"

            log_btn.click(
                fn=_save_log,
                inputs=[log_date, log_foods, log_activities, log_score, log_notes],
                outputs=log_status
            )
            xref_btn.click(
                fn=cross_reference,
                inputs=log_foods,
                outputs=xref_output
            )

        # ── Tab 3: Timeline ─────────────────────────────────────────────
        with gr.Tab("Symptom Timeline"):
            gr.Markdown(
                "### Flare Pattern Analysis\n"
                "Shows your skin score over time and the foods most commonly eaten "
                f"in the 3 days before a flare (score ≥ 7)."
            )
            refresh_btn   = gr.Button("Refresh Chart", variant="secondary")
            timeline_plot = gr.Plot()
            refresh_btn.click(fn=build_plot, inputs=[], outputs=timeline_plot)

# Launch the Gradio app
if __name__ == "__main__":
    demo.launch(
        inbrowser=True,
        theme=gr.themes.Soft(primary_hue="blue", neutral_hue="slate"),
        css=CSS
    )