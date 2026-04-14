import re

def split_into_paragraphs(text):
    """
    - Splits the input text into paragraphs.
    - Each paragraph is separated by a newline, and we filter out any empty lines.
    - Returns a list of paragraph strings.
    """
    return [p.strip() for p in text.split("\n") if p.strip()]

def chunk_text(text, max_words=400, overlap=80):
    """
    Breaks long text into smaller, overlapping chunks for better search and retrieval.

    - Each chunk contains up to 'max_words' words.
    - Chunks overlap by 'overlap' words to preserve context between them.
    - This helps the search system find relevant information even if it spans across chunk boundaries.

    Returns a list of chunk strings.
    """
    paragraphs = split_into_paragraphs(text)

    chunks = []
    current = []
    current_len = 0

    for para in paragraphs:
        words = para.split()
        if not words:
            continue

        # If adding this paragraph does not exceed the max word limit, add it to the current chunk
        if current_len + len(words) <= max_words:
            current.append(para)
            current_len += len(words)
        else:
            # Save the current chunk
            chunks.append(" ".join(current))

            # Start a new chunk, beginning with the last 'overlap' words from the previous chunk
            overlap_words = " ".join(current).split()[-overlap:]
            current = [" ".join(overlap_words), para]
            current_len = len(overlap_words) + len(words)

    # Add any remaining text as the last chunk
    if current:
        chunks.append(" ".join(current))

    return chunks