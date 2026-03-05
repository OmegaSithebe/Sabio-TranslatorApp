"""
utils/file_utils.py
File validation and display helpers.
"""

import os
from typing import Tuple, Optional

MAX_FILE_SIZE       = 200 * 1024 * 1024   # 200 MB
ALLOWED_EXTENSIONS  = {".pdf", ".docx", ".xlsx", ".xls"}

_TYPE_LABELS = {
    ".pdf":  "PDF Document",
    ".docx": "Word Document",
    ".xlsx": "Excel Spreadsheet",
    ".xls":  "Excel Spreadsheet (Legacy)",
}
_TYPE_BADGES = {
    ".pdf":  "PDF",
    ".docx": "DOCX",
    ".xlsx": "XLSX",
    ".xls":  "XLS",
}


def get_file_extension(filename: str) -> Optional[str]:
    if not filename:
        return None
    return os.path.splitext(filename)[1].lower()


def allowed_file_type(filename: str) -> bool:
    ext = get_file_extension(filename)
    return ext in ALLOWED_EXTENSIONS if ext else False


def get_file_type_display(extension: str) -> str:
    return _TYPE_LABELS.get(extension.lower(), "Unknown File Type")


def get_file_icon(filename: str) -> str:
    ext = get_file_extension(filename)
    return _TYPE_BADGES.get(ext, "FILE")


def validate_file(file) -> Tuple[bool, str]:
    if file is None:
        return False, "No file provided."
    if hasattr(file, "size") and file.size > MAX_FILE_SIZE:
        mb = file.size / (1024 * 1024)
        return False, f"File exceeds the 200 MB limit ({mb:.1f} MB uploaded)."
    if not allowed_file_type(file.name):
        ext = get_file_extension(file.name) or "unknown"
        return False, f"'{ext}' is not supported. Please upload a PDF, DOCX, or Excel file."
    return True, "Valid"


def format_file_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 ** 2):.1f} MB"
