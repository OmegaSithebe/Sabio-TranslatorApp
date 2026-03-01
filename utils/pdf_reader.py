import fitz  # PyMuPDF

def extract_pdf_text(file):
    text = ""
    try:
        pdf = fitz.open(stream=file.read(), filetype="pdf")
        for page in pdf:
            text += page.get_text()
        pdf.close()
        return text
    except Exception:
        return None