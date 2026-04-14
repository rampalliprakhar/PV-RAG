import os
import faiss
import pickle
from embed import embed
from utils.chunking import chunk_text
from loaders import get_loader
from config import *

def build_index(embeddings, dim):
    """
    Build a FAISS index from the given embeddings.
    Uses a fast 'flat' index for small datasets, and a memory-efficient IVFPQ index for large ones.
    """
    n = len(embeddings)
    nlist = 100
    if n < nlist * 39:
        print(f"[warn] Only {n} vectors: using flat index (need >{nlist*39} for IVFPQ)")
        index = faiss.IndexFlatIP(dim)
    else:
        quantizer = faiss.IndexFlatIP(dim)
        index = faiss.IndexIVFPQ(quantizer, dim, nlist, 8, 8)
        index.train(embeddings)
    index.add(embeddings)
    return index

def ingest(folder):
    """
    Go through all files in the given folder, extract and chunk their text
    embed the chunks, and build a search index for fast retrieval.
    """
    texts = []
    metadata = []

    # Recursively walk through all files in the folder
    for root, _, files in os.walk(folder):
        for f in files:
            path = os.path.join(root, f)

            # Pick the right loader for each file type (.txt, .md, .pdf, .docx)
            loader = get_loader(path)
            if not loader:
                continue

            try:
                # Extract and clean the text from the file
                content = loader.load(path)
            except Exception as e:
                print(f"Error loading {path}: {e}")
                continue

            # Split the text into overlapping chunks for better search accuracy
            chunks = chunk_text(content, CHUNK_SIZE, CHUNK_OVERLAP)

            for i, c in enumerate(chunks):
                texts.append(c)
                metadata.append({
                    "path": path,           # File path
                    "chunk_id": i,          # Which chunk in the file
                    "content": c            # The actual text chunk
                })

    if not texts:
        print("No documents found to ingest.")
        return

    # Convert all text chunks into embeddings (vectors)
    embeddings = embed(texts)
    dim = embeddings.shape[1]
    index = build_index(embeddings, dim)

    # Save the search index and metadata for later use
    os.makedirs("index", exist_ok=True)
    faiss.write_index(index, "index/faiss.index")

    with open("index/metadata.pkl", "wb") as f:
        pickle.dump(metadata, f)

    print(f"Ingestion complete. {len(texts)} chunks indexed.")