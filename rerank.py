from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from config import RERANK_MODEL

# These variables will hold the loaded model and tokenizer to avoid reloading on every call
_tokenizer = None
_model = None

def load_model():
    """
    Loads the cross-encoder reranker model and tokenizer from HuggingFace.
    Only loads once and reuses for future calls.
    """
    global _tokenizer, _model
    if _model is None:
        # Load the tokenizer (turns text into model input)
        _tokenizer = AutoTokenizer.from_pretrained(RERANK_MODEL)
        # Load the reranker model (scores relevance between query and chunk)
        _model = AutoModelForSequenceClassification.from_pretrained(RERANK_MODEL)
        # Set the model to evaluation mode (faster, no training)
        _model.eval()
    return _tokenizer, _model

def rerank(query, docs, top_k=5):
    """
    Given a query and a list of document chunks, rerank them by relevance using a cross-encoder model

    Steps:
    1. For each chunk, pair it with the query
    2. The model scores each (query, chunk) pair for relevance
    3. Sort all chunks by their score, highest first
    4. Return the top_k most relevant chunks

    Returns:
        List of dicts, sorted by relevance
    """
    tokenizer, model = load_model()
    # Prepare input pairs: (query, chunk content)
    pairs = [(query, d["content"]) for d in docs]
    # Tokenize all pairs for the model
    inputs = tokenizer(pairs, padding=True, truncation=True, return_tensors="pt")
    with torch.no_grad():
        # Get relevance scores from the model
        scores = model(**inputs).logits.squeeze(-1)
        # If only one doc, ensure scores is still a list
        if scores.dim() == 0:
            scores = scores.unsqueeze(0)
    # Pair each score with its documents
    scored = list(zip(scores.tolist(), docs))
    # Sort by score, highest first
    scored.sort(key=lambda x: x[0], reverse=True)
    # Return only the document part, top_k results
    return [d for _, d in scored[:top_k]]