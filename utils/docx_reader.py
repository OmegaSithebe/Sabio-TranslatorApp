from docx import Document
from io import BytesIO

def extract_docx_text(file):
    try:
        doc = Document(file)
        text = "\n".join([p.text for p in doc.paragraphs])
        return text
    except Exception:
        return None


def create_translated_docx(text):
    buffer = BytesIO()
    doc = Document()
    for line in text.split("\n"):
        doc.add_paragraph(line)
    doc.save(buffer)
    buffer.seek(0)
    return buffer