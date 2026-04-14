from .text_loader import TextLoader
from .markdown_loader import MarkdownLoader
from .pdf_loader import PDFLoader
from .docx_loader import DocxLoader

def get_loader(path):
    # Determine the file type based on the extension and return the appropriate loader
    ext = path.lower()
    if ext.endswith(".txt"):   return TextLoader()
    if ext.endswith(".md"):    return MarkdownLoader()
    if ext.endswith(".pdf"):   return PDFLoader()
    if ext.endswith(".docx"):  return DocxLoader()
    # If we do not recognize the file type, return None to indicate we cannot load it
    return None