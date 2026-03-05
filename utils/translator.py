"""
utils/translator.py

Language detection and fast batched translation.

Speed strategy
--------------
Instead of one HTTP request per paragraph/span, we:

1. DEDUPLICATE  — identical strings are translated only once.
2. BATCH        — pack many short strings into a single request
                  using a separator trick (strings joined with a
                  unique sentinel, sent as one chunk, split on return).
3. PARALLELISE  — send multiple batches concurrently with a thread pool.

A 40-page document that previously made ~800 sequential requests now
makes ~8-10 parallel batched requests — typically 10-20× faster.
"""

import os
import re
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional
import streamlit as st

SUPPORTED_LANGUAGES: dict[str, str] = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "nl": "Dutch",
    "ru": "Russian",
    "zh": "Chinese (Simplified)",
    "ja": "Japanese",
    "ko": "Korean",
    "ar": "Arabic",
    "hi": "Hindi",
    "tr": "Turkish",
    "pl": "Polish",
    "uk": "Ukrainian",
    "vi": "Vietnamese",
    "th": "Thai",
    "cs": "Czech",
    "el": "Greek",
    "sv": "Swedish",
    "da": "Danish",
    "fi": "Finnish",
    "no": "Norwegian",
    "hu": "Hungarian",
    "ro": "Romanian",
    "bg": "Bulgarian",
    "id": "Indonesian",
    "ms": "Malay",
}

# ── Tuning knobs ───────────────────────────────────────────────────────────
# Max characters packed into a single Google Translate request.
# Google's hard limit is 5 000; we stay safely below it.
_BATCH_CHARS   = 4_000

# Number of parallel translation threads.
# 8 is a safe default that avoids rate-limiting on most connections.
_WORKERS       = 8

# Sentinel used to join/split strings within a single request.
# Must be something that (a) won't appear in real text and (b) survives
# round-tripping through Google Translate unchanged.
_SEP           = " ⏎⏎ "
_SEP_PATTERN   = re.compile(r"\s*⏎⏎\s*")

_RETRIES       = 3
_RETRY_DELAY   = 1.0


# ══════════════════════════════════════════════════════════════════════════
# Public API
# ══════════════════════════════════════════════════════════════════════════

def detect_language(text: str) -> Optional[str]:
    if not text or len(text.strip()) < 10:
        return None
    try:
        from langdetect import detect, DetectorFactory
        DetectorFactory.seed = 42
        sample = " ".join(text.split()[:200])
        code   = detect(sample)
        if code.startswith("zh"):
            return "zh"
        code = code.split("-")[0]
        return code if code in SUPPORTED_LANGUAGES else None
    except Exception:
        return None


def translate_text(text: str, source: str, target: str) -> Optional[str]:
    """Translate a single plain-text string (used by the Quick Text panel)."""
    if not text or not text.strip():
        return ""
    source = _normalise(source, text)
    target = target.split("-")[0].lower()
    if source == target:
        return text
    return _translate_one(text, source, target)


def translate_many(
    strings: list[str],
    source: str,
    target: str,
) -> dict[str, str]:
    """
    Translate a list of strings efficiently.

    Returns a dict mapping each original string to its translation.
    Strings that should not be translated are returned unchanged.
    Identical strings are translated only once.

    This is the function called by the PDF / DOCX / XLSX readers.
    """
    if not strings:
        return {}

    source = _normalise(source, " ".join(strings[:20]))
    target = target.split("-")[0].lower()

    # Separate strings that need translation from those that don't
    to_translate: list[str] = []
    result: dict[str, str]  = {}

    for s in strings:
        if not s or not s.strip() or source == target:
            result[s] = s
        else:
            to_translate.append(s)

    if not to_translate:
        return result

    # Deduplicate — translate each unique string only once
    unique = list(dict.fromkeys(to_translate))   # preserves insertion order

    # Pack unique strings into batches
    batches = _make_batches(unique)

    # Translate batches in parallel
    translated_unique: dict[str, str] = {}
    lock = threading.Lock()

    with ThreadPoolExecutor(max_workers=min(_WORKERS, len(batches))) as pool:
        futures = {
            pool.submit(_translate_batch, batch, source, target): batch
            for batch in batches
        }
        for future in as_completed(futures):
            batch_result = future.result()   # dict[original → translated]
            with lock:
                translated_unique.update(batch_result)

    # Map every original string (including duplicates) to its translation
    for s in to_translate:
        result[s] = translated_unique.get(s, s)

    return result


def get_language_name(code: str) -> str:
    return SUPPORTED_LANGUAGES.get(code, code)


# ══════════════════════════════════════════════════════════════════════════
# Batching helpers
# ══════════════════════════════════════════════════════════════════════════

def _make_batches(strings: list[str]) -> list[list[str]]:
    """
    Group strings into batches where each batch's joined length stays
    under _BATCH_CHARS.  Single strings longer than _BATCH_CHARS get
    their own batch.
    """
    batches: list[list[str]] = []
    current: list[str]       = []
    current_len              = 0
    sep_len                  = len(_SEP)

    for s in strings:
        s_len = len(s)
        # Would adding this string exceed the batch limit?
        needed = s_len + (sep_len if current else 0)
        if current and current_len + needed > _BATCH_CHARS:
            batches.append(current)
            current     = []
            current_len = 0
        current.append(s)
        current_len += s_len + (sep_len if len(current) > 1 else 0)

    if current:
        batches.append(current)

    return batches


def _translate_batch(batch: list[str], source: str, target: str) -> dict[str, str]:
    """
    Translate a batch of strings using the separator trick.

    We join them with _SEP, send as one request, split on the returned
    separator.  If the split count doesn't match (rare — happens when
    Google occasionally drops the separator), we fall back to translating
    each string individually.
    """
    if len(batch) == 1:
        original    = batch[0]
        translated  = _translate_one(original, source, target)
        return {original: translated or original}

    joined     = _SEP.join(batch)
    translated = _translate_one(joined, source, target)

    if not translated:
        # Full batch failed — fall back one-by-one
        return {s: (_translate_one(s, source, target) or s) for s in batch}

    parts = _SEP_PATTERN.split(translated)

    if len(parts) == len(batch):
        return {orig: trans for orig, trans in zip(batch, parts)}

    # Separator count mismatch — fall back one-by-one to stay correct
    result = {}
    for s in batch:
        result[s] = _translate_one(s, source, target) or s
    return result


def _translate_one(text: str, source: str, target: str) -> Optional[str]:
    """Single-string translation with retry logic."""
    try:
        from deep_translator import GoogleTranslator
    except ImportError:
        st.error("deep-translator not installed. Run: pip install deep-translator")
        return None

    for attempt in range(_RETRIES):
        try:
            result = GoogleTranslator(source=source, target=target).translate(text)
            if result:
                return result
        except Exception as exc:
            err = str(exc)
            if "429" in err:
                time.sleep(_RETRY_DELAY * (attempt + 2))   # back off harder on rate limit
            elif attempt < _RETRIES - 1:
                time.sleep(_RETRY_DELAY)
            else:
                return None
    return None


def _normalise(source: str, sample_text: str) -> str:
    """Resolve 'auto' to a real language code."""
    if source == "auto":
        return detect_language(sample_text) or "en"
    return source.split("-")[0].lower()
