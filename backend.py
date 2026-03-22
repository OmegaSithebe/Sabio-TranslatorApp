from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import Optional
import io

from utils.translator import (
    translate_text,
    translate_many,
    detect_language,
    SUPPORTED_LANGUAGES,
)
from utils.file_utils import validate_file, get_file_extension
from utils.pdf_reader import extract_pdf_text, translate_pdf_inplace
from utils.docx_reader import extract_docx_text, translate_docx_inplace
from utils.excel_reader import extract_excel_text, translate_xlsx_inplace

app = FastAPI(title="Sabio Translator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/languages")
def get_languages():
    return {"languages": SUPPORTED_LANGUAGES}


@app.post("/api/translate-text")
def translate_text_endpoint(
    text: str = Form(...),
    source: Optional[str] = Form("auto"),
    target: str = Form("en"),
):
    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="Text is required")

    source_norm = source
    if source_norm == "auto":
        detected = detect_language(text)
        source_norm = detected or "en"

    if source_norm == target:
        return {"translated": text, "source": source_norm, "target": target}

    result = translate_text(text, source_norm, target)
    if result is None:
        raise HTTPException(status_code=500, detail="Translation failed")
    return {"translated": result, "source": source_norm, "target": target}


@app.post("/api/translate-document")
def translate_document_endpoint(
    file: UploadFile = File(...),
    target: str = Form("en"),
    source: str = Form("auto"),
):
    if file is None:
        raise HTTPException(status_code=400, detail="No file uploaded")

    ok, msg = validate_file(file)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    ext = get_file_extension(file.filename)
    if ext not in [".pdf", ".docx", ".xlsx"]:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    content = file.file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    try:
        buffer = io.BytesIO(content)
        if ext == ".pdf":
            sample = extract_pdf_text(buffer)
        elif ext == ".docx":
            sample = extract_docx_text(buffer)
        else:
            sample = extract_excel_text(buffer)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not read file: {exc}")

    if not sample or not sample.strip():
        raise HTTPException(status_code=400, detail="No readable text detected in file")

    if source == "auto":
        source = detect_language(sample) or "en"

    if source == target:
        raise HTTPException(status_code=400, detail="Source and target language cannot be the same")

    try:
        buffer.seek(0)
        if ext == ".pdf":
            out = translate_pdf_inplace(
                buffer,
                translate_fn=lambda text: translate_text(text, source, target),
                translate_many_fn=lambda strings: translate_many(strings, source, target),
            )
            media_type = "application/pdf"
        elif ext == ".docx":
            out = translate_docx_inplace(
                buffer,
                translate_fn=lambda text: translate_text(text, source, target),
                translate_many_fn=lambda strings: translate_many(strings, source, target),
            )
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        else:
            out = translate_xlsx_inplace(
                buffer,
                translate_fn=lambda text: translate_text(text, source, target),
                translate_many_fn=lambda strings: translate_many(strings, source, target),
            )
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

        if out is None:
            raise HTTPException(status_code=500, detail="Translation failed")

    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Translation failed: {exc}")

    out.seek(0)

    filename = f"translated_{file.filename}"
    return StreamingResponse(
        out,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename=\"{filename}\""},
    )
