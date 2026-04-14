from .base import BaseLoader
from utils.text_clean import clean_text

class TextLoader(BaseLoader):
    def load(self, path):
        # Try to open the file using several common text encodings
        for encoding in ("utf-8", "windows-1252", "latin-1"):
            try:
                with open(path, "r", encoding=encoding) as f:
                    # Clean the text to remove extra whitespace and normalize it before returning
                    return clean_text(f.read())
            except UnicodeDecodeError:
                # If we hit a decoding error, try the next encoding
                continue
        # If we exhausted all encodings without success, raise an error
        raise ValueError(f"Could not decode file with any supported encoding: {path}")