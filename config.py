import os

# Name of the embedding model used to convert text into vectors for search
EMBED_MODEL = "BAAI/bge-small-en-v1.5"

# Name of the reranking model used to sort search results by relevance
RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

# Maximum number of words in each text chunk (smaller = more precise, larger = more context) 
CHUNK_SIZE = 400

# Number of words to overlap between chunks (helps preserve context across splits)
CHUNK_OVERLAP = 80

# Number of candidate chunks to fetch from the search index before reranking.
TOP_K_RETRIEVE = 50

# Number of top chunks to use as context for the final answer.
TOP_K_FINAL = 5

# NCBI / PubMed
NCBI_EMAIL = os.environ.get("NCBI_EMAIL", "email@example.com")
# NCBI API key
NCBI_API_KEY = os.environ.get("NCBI_API_KEY", None)

# Disease Scope
PV_QUERY = "pemphigus vulgaris"

# Records to pull
PUBMED_MAX_RESULTS = 10_000
PMC_MAX_RESULTS = 3_000

PUBMED_DATA_FOLDER = "data/pubmed"
PMC_DATA_FOLDER = "data/pmc"