import markdown
from bs4 import BeautifulSoup
from .base import BaseLoader
from utils.text_clean import clean_text

class MarkdownLoader(BaseLoader):
    def load(self, path):
        # Try to open the file using several common text encodings
        # This helps handle files created on different systems (Windows, Mac, Linux)
        for encoding in ("utf-8", "windows-1252", "latin-1"):
            try:
                with open(path, "r", encoding=encoding) as f:
                    md = f.read()
                # Stop trying encodings once we successfully read the file
                break
            except UnicodeDecodeError:
                # If we hit a decoding error, try the next encoding
                continue
        else:
            # If we cannot read the file, we cannot proceed with loading it, so we raise an exception to indicate this failure
            raise ValueError(f"Could not decode file: {path}")
        # Convert markdown to HTML, then extract text using BeautifulSoup
        html = markdown.markdown(md)
        soup = BeautifulSoup(html, "html.parser")
        # Clean the extracted text to remove extra whitespace and normalize it
        return clean_text(soup.get_text())