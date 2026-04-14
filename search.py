import faiss
import os
import pickle
from embed import embed_query
from config import TOP_K_RETRIEVE

# These variables will hold the loaded FAISS index and metadata in memory for fast access
_index = None
_metadata = None

def load():
    """
    Loads the FAISS index (for fast similarity search) and the metadata (info about each text chunk) from disk. Uses cached versions if already loaded.
    """
    global _index, _metadata
    if _index is None:
        if not os.path.exists("index/faiss.index"):
            return None, None   # index not built yet
        _index = faiss.read_index("index/faiss.index")
        with open("index/metadata.pkl", "rb") as f:
            _metadata = pickle.load(f)
    return _index, _metadata

def search(query: str):
    """
    Givn a user query (question), find the most relevant text chunks from your indexed documents.

    Steps:
    1. Convert the query into a vector (using the embedding model)
    2. Search the FAISS index for the most similar vectors (text chunks)
    3. Return the corresponding metadata for the top results

    Returns:
        List of dicts, each with 'path', 'chunk_id', and 'content'
    """
    index, metadata = load()
    if index is None:
        return []               # triggers the "Run ingestion first" message in app.py
    query_vec = embed_query(query)
    D, I = index.search(query_vec, TOP_K_RETRIEVE)
    return [metadata[i] for i in I[0] if i != -1]