# Sabio Translator App (React + FastAPI)

This is a production-ready translation service that uses OpenAI for text translation and preserves formatting for PDF/DOCX/XLSX using Python document libraries.

## Project structure
- `backend.py` – FastAPI backend endpoints for text/document translation.
- `utils/` – Shared document parsers and translation pipeline.
- `frontend/` – React/Vite UI.

## Requirements
- Python 3.11+
- Node.js 18+
- OpenAI API key (`OPENAI_API_KEY`)

## Setup
1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Install frontend dependencies:
   ```bash
   cd frontend && npm install
   ```
3. Set OpenAI API key:
   ```bash
   export OPENAI_API_KEY="sk-..."
   ```
4. Run backend:
   ```bash
   uvicorn backend:app --host 0.0.0.0 --port 8000
   ```
5. Run frontend:
   ```bash
   cd frontend
   npm run dev -- --host 0.0.0.0
   ```
6. Open `http://localhost:5173`.

## API
- `GET /api/languages` returns supported language codes.
- `POST /api/translate-text` form data: `text`, `source`, `target`.
- `POST /api/translate-document` multipart form: `file`, `source`, `target`.

## Notes
- For scanned PDFs, install `pytesseract` and `Pillow`.
- The OpenAI model used in code is `gpt-4.1-mini`; adjust in `utils/translator.py` if needed.
