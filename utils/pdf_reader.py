"""
utils/pdf_reader.py

In-place PDF translation using PyMuPDF (fitz).

Speed approach
--------------
Previous: translate each span individually → one HTTP call per span.
Now:
  Pass 1 — walk every page, collect ALL text spans into one list.
  Pass 2 — hand the whole list to translate_many() which deduplicates,
            batches, and translates in parallel threads.
  Pass 3 — apply redactions and re-insert translated text.

This turns ~800 sequential requests into ~10 parallel batched requests.

Images, logos, table borders, and all non-text content are untouched.
"""

import io
import logging
from typing import Callable, Optional


def extract_pdf_text(file) -> Optional[str]:
    """Extract plain text for language detection (structure not needed)."""
    try:
        import fitz
        file.seek(0)
        doc   = fitz.open(stream=file.read(), filetype="pdf")
        parts = [page.get_text().strip() for page in doc if page.get_text().strip()]
        doc.close()
        return "\n\n".join(parts) or ""
    except Exception as exc:
        logging.error(f"Could not read PDF: {exc}")
        return None


def translate_pdf_inplace(
    file,
    translate_fn:    Callable[[str], Optional[str]],
    translate_many_fn: Optional[Callable[[list[str]], dict[str, str]]] = None,
) -> Optional[io.BytesIO]:
    """
    Translate a PDF in-place; every image, logo, and graphical element
    is preserved exactly.

    Parameters
    ----------
    file              : Seekable uploaded file.
    translate_fn      : Single-string fallback (used for OCR path).
    translate_many_fn : Preferred fast path — takes list[str], returns
                        dict mapping original → translated.
    """
    try:
        import fitz
    except ImportError:
        raise ImportError("PyMuPDF not installed. Run: pip install pymupdf")

    try:
        file.seek(0)
        doc = fitz.open(stream=file.read(), filetype="pdf")
    except Exception as exc:
        raise RuntimeError(f"Could not open PDF: {exc}") from exc

    has_text = any(page.get_text().strip() for page in doc)

    if not has_text:
        logging.warning(
            "This PDF has no selectable text (fully scanned). "
            "Install pytesseract and Pillow for OCR support."
        )
        result = _translate_scanned(doc, translate_fn)
        doc.close()
        return result

    try:
        # ── Pass 1: collect every translatable span from all pages ────────
        page_spans: list[list[dict]] = []
        all_originals: list[str]     = []

        for page in doc:
            blocks = page.get_text(
                "dict", flags=fitz.TEXT_PRESERVE_WHITESPACE
            )["blocks"]
            spans: list[dict] = []

            for block in blocks:
                if block.get("type") != 0:      # skip image blocks
                    continue
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span["text"].strip()
                        if not text or _skip(text):
                            continue
                        spans.append({
                            "original":  text,
                            "rect":      fitz.Rect(span["bbox"]),
                            "font_size": span["size"],
                            "color":     _unpack_color(span.get("color", 0)),
                            "font_name": _safe_font(span.get("font", "helv")),
                        })
                        all_originals.append(text)

            page_spans.append(spans)

        if not all_originals:
            # Nothing to translate — return original unchanged
            buf = io.BytesIO()
            doc.save(buf, garbage=2, deflate=True)
            doc.close()
            buf.seek(0)
            return buf

        # ── Pass 2: batch-translate all unique strings in parallel ─────────
        unique = list(dict.fromkeys(all_originals))   # deduplicated, ordered

        if translate_many_fn:
            translations = translate_many_fn(unique)
        else:
            # Slow fallback
            translations = {t: (translate_fn(t) or t) for t in unique}

        # ── Pass 3: apply redactions and re-insert translated text ─────────
        for page, spans in zip(doc, page_spans):
            to_apply = []
            for span in spans:
                translated = translations.get(span["original"], "").strip()
                if not translated or translated == span["original"]:
                    continue
                to_apply.append({**span, "translated": translated})

            # Redact originals
            for item in to_apply:
                page.add_redact_annot(item["rect"], fill=(1, 1, 1))
            page.apply_redactions()

            # Re-insert translations
            for item in to_apply:
                _insert_text(page, item)

        buf = io.BytesIO()
        doc.save(buf, garbage=2, deflate=True)
        doc.close()
        buf.seek(0)
        return buf

    except Exception as exc:
        doc.close()
        raise RuntimeError(f"Error translating PDF: {exc}") from exc


# ── Text insertion helper ─────────────────────────────────────────────────

def _insert_text(page, item: dict) -> None:
    """Insert translated text at the original span position."""
    kwargs = dict(
        fontsize  = item["font_size"],
        color     = item["color"],
        fontname  = item["font_name"],
    )
    try:
        page.insert_text(item["rect"].tl, item["translated"], **kwargs)
    except Exception:
        try:
            page.insert_text(item["rect"].tl, item["translated"],
                             fontsize=item["font_size"], color=item["color"],
                             fontname="helv")
        except Exception:
            pass


# ── Scanned PDF (OCR) path ────────────────────────────────────────────────

def _translate_scanned(doc, translate_fn: Callable) -> Optional[io.BytesIO]:
    try:
        import pytesseract
        from PIL import Image
        import io as _io
    except ImportError:
        raise ImportError(
            "Scanned PDF detected. Install pytesseract and Pillow: "
            "pip install pytesseract Pillow"
        )

    for page in doc:
        mat      = page.get_pixmap(dpi=200)
        img      = Image.open(_io.BytesIO(mat.tobytes("png")))
        ocr_text = pytesseract.image_to_string(img).strip()
        if not ocr_text:
            continue
        translated = translate_fn(ocr_text)
        if translated:
            page.insert_textbox(page.rect, translated,
                                fontsize=11, fontname="helv", color=(0, 0, 0))

    buf = io.BytesIO()
    doc.save(buf, garbage=2, deflate=True)
    buf.seek(0)
    return buf


# ── Helpers ───────────────────────────────────────────────────────────────

def _skip(text: str) -> bool:
    import re
    if len(text) <= 1:
        return True
    if re.fullmatch(r"[\d\s.,\-/\\:;()+%$€£@#&*=<>_|~`'\"!?]+", text):
        return True
    if re.match(r"https?://\S+", text):
        return True
    return False


def _unpack_color(packed: int) -> tuple:
    r = ((packed >> 16) & 0xFF) / 255.0
    g = ((packed >>  8) & 0xFF) / 255.0
    b = ((packed      ) & 0xFF) / 255.0
    return (r, g, b)


def _safe_font(font_name: str) -> str:
    name = font_name.lower()
    if any(k in name for k in ("courier", "cour", "mono", "consol")):
        if "bold" in name and "italic" in name: return "courbi"
        if "bold" in name:                       return "courb"
        if "italic" in name or "oblique" in name: return "couri"
        return "cour"
    if any(k in name for k in ("times", "serif", "georgia")):
        if "bold" in name and "italic" in name: return "timbi"
        if "bold" in name:                       return "timb"
        if "italic" in name or "oblique" in name: return "timi"
        return "timr"
    if any(k in name for k in ("helvetica", "arial", "sans")):
        if "bold" in name and "italic" in name: return "heboit"
        if "bold" in name:                       return "hebo"
        if "italic" in name or "oblique" in name: return "hebi"
        return "helv"
    return "helv"
