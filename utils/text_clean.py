import re

def clean_text(text: str) -> str:
    """
    Cleans and normalizes text for better processing.

    - Replaces multiple spaces and tabs with a single space.
    - Collapses multiple newlines into a maximum of two to preserve paragraph breaks.
    - Strips leading and trailing whitespace.

    This helps ensure that the text is consistent and easy to work with for search and language models.
    """
    # Replace runs of spaces/tabs with a single space
    text = re.sub(r"[ \t]+", " ", text)
    # Collapse 3+ newlines to paragraph break
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Remove any extra spaces at the start or end
    return text.strip()