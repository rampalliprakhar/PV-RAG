import pdfplumber
import re
from .base import BaseLoader
from utils.text_clean import clean_text

# This regex looks for common PDF syntax patterns that indicate the text is not properly extracted
_PDF_GARBAGE = re.compile(r"<<\s*/Type|endobj|obj\s*<<|/Filter\s*/FlateDecode")

class PDFLoader(BaseLoader):
    def load(self, path):
        text = ""
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                # Extract text from each page. If the page is empty, use an empty string
                page_text = page.extract_text() or ""
                # Skip pages that contain raw PDF syntax, which indicates the text was not properly extracted
                if _PDF_GARBAGE.search(page_text):
                    continue
                # Remove the first and last lines if the page is long
                lines = page_text.split("\n")
                if len(lines) > 5:
                    lines = lines[1:-1]
                text += "\n".join(lines) + "\n"
        # Clean the text before returning
        return clean_text(text)