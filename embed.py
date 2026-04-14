from sentence_transformers import SentenceTransformer
import numpy as np
from config import EMBED_MODEL

# Global variable to hold the loaded model instance
_model = None

def get_model():
    """
    Loads the embedding model if it has not been loaded yet.
    This saves memory and speeds up repeated use.
    """
    global _model
    if _model is None:
        # Load the model specified in config.py
        _model = SentenceTransformer(EMBED_MODEL)
    return _model


def embed(texts, batch_size=32):
    """
    Converts a list of texts into numerical vectors (embeddings) that capture their meaning.
    These embeddings are used for searching and comparing text.

    Args:
        texts (List[str]): The input texts to embed
        batch_size (int): How many texts to process at once (higher = faster, but uses more memory)

    Returns:
        np.ndarray: shape (n, dim) 
        An array of embedding vectors, where n is the number of input texts and dim is the size of each embedding.
    """

    model = get_model()

    # Generate embeddings for all texts, normalize them for better search, and show a progress bar
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        normalize_embeddings=True,
        show_progress_bar=True
    )

    return np.array(embeddings)


def embed_query(query: str):
    """
    Converts a user query into an embedding, with special handling for BGE models.
    BGE models work best if we add 'query: ' in front of the question.

    Args:
        query (str): The user's search query

    Returns:
        np.ndarray: The embedding for the query, ready for searching
    """

    model = get_model()

    # Add the recommended prefix for best results with BGE models
    query = "query: " + query

    embedding = model.encode(
        [query],
        normalize_embeddings=True
    )

    return embedding