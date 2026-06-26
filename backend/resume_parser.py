import fitz 
from docx import Document

def extract_pdf_text(file_bytes:bytes) -> str:
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text = ""

    for page in doc:
        text += page.get_text()

    return text.strip()

def extract_docx_text(file_bytes:bytes) -> str:
    doc = Document(file_bytes)
    text = ""

    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"

    return text.strip()

def extract_resume_text(file_bytes: bytes, filename: str) -> str:
    if filename.endswith(".pdf"):
        return extract_pdf_text(file_bytes)
    
    raise ValueError("Unsupported file format. Only PDF files are supported.")

