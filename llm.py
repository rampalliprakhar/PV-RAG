import os
from llama_cpp import Llama

_llm = None

def get_llm():
    """
    Load the local LLM only once and reuse it.
    This saves memory and speeds up repeated queries.
    """
    global _llm
    if _llm is None:
        model_path = "models/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found: {model_path}")
        _llm = Llama(
            model_path=model_path,
            n_ctx=4096,                     # Max tokens the model can see at once
            n_threads=os.cpu_count(),       # Use all CPU cores for speed
            verbose=False                   # Hide loading logs
        )
    return _llm

def generate(prompt, max_tokens=512):
    """
    Generate an answer from the LLM, making sure the prompt fits in the model's context window
    """
    llm = get_llm()
    # Truncate prompt if it would exceed the context window
    token_ids = llm.tokenize(prompt.encode())
    # Leave room for the answer
    max_prompt_tokens = llm.n_ctx() - max_tokens - 10
    if len(token_ids) > max_prompt_tokens:
        # If the prompt is too long, truncate it to fit
        token_ids = token_ids[:max_prompt_tokens]
        prompt = llm.detokenize(token_ids).decode("utf-8", errors="ignore")
    output = llm(prompt, max_tokens=max_tokens, temperature=0.7)
    return output["choices"][0]["text"]