from search import search
from rerank import rerank
from llm import generate
from config import *

def ask(query):
    """
    Main RAG pipeline:
    1. Search for relevant document chunks using the query embedding
    2. Rerank the retrieved chunks to find the most relevant ones
    3. Build a prompt that includes the top relevant chunks as context and the user's question
    4. Ask the LLM to generate an answer based on that prompt
    """
    candidates = search(query)
    if not candidates:
        return "No indexed literature found. Run: python main.py ingest data/"
    top_docs = rerank(query, candidates, TOP_K_FINAL)
    context = "\n\n".join([d["content"] for d in top_docs])

    # The prompt tells the LLM to only use the provided context, not to make things up
    prompt = (
        f"[INST] You are a medical assistant specializing in pemphigus vulgaris. "
        f"Answer ONLY using the provided PubMed/PMC context. "
        f"If the answer is not supported by the context, say 'This is not covered in the indexed literature.'\n\n"
        f"Context:\n{context}\n\nQuestion: {query} [/INST]"
    )

    return generate(prompt)