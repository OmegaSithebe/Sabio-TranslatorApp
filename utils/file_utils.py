# utils/file_utils.py
import os
from typing import Tuple, Optional
import streamlit as st

# File size limits (in bytes)
MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.xlsx', '.xls', '.xlsm'}

def allowed_file_type(filename: str) -> bool:
    """
    Check if file type is allowed
    
    Args:
        filename: Name of the file
        
    Returns:
        Boolean indicating if file type is allowed
    """
    if not filename:
        return False
    
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS

def get_file_extension(filename: str) -> Optional[str]:
    """Get file extension"""
    if not filename:
        return None
    return os.path.splitext(filename)[1].lower()

def get_file_type_display(extension: str) -> str:
    """Get user-friendly file type name"""
    type_map = {
        '.pdf': 'PDF Document',
        '.docx': 'Word Document',
        '.xlsx': 'Excel Spreadsheet',
        '.xls': 'Excel Spreadsheet (Legacy)',
        '.xlsm': 'Excel Macro-Enabled'
    }
    return type_map.get(extension.lower(), 'Unknown')

def validate_file(file) -> Tuple[bool, str]:
    """
    Validate uploaded file
    
    Args:
        file: Uploaded file object
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if file is None:
        return False, "No file uploaded"
    
    # Check file size
    if hasattr(file, 'size') and file.size > MAX_FILE_SIZE:
        size_mb = file.size / (1024 * 1024)
        return False, f"File too large ({size_mb:.1f}MB). Maximum size is 200MB"
    
    # Check file type
    if not allowed_file_type(file.name):
        ext = get_file_extension(file.name)
        return False, f"File type {ext} not supported. Please upload PDF, DOCX, or Excel files"
    
    return True, "File valid"

def format_file_size(size_in_bytes: int) -> str:
    """Format file size for display"""
    if size_in_bytes < 1024:
        return f"{size_in_bytes} B"
    elif size_in_bytes < 1024 * 1024:
        return f"{size_in_bytes / 1024:.1f} KB"
    else:
        return f"{size_in_bytes / (1024 * 1024):.1f} MB"

def get_file_icon(filename: str) -> str:
    """Get appropriate emoji icon for file type"""
    ext = get_file_extension(filename)
    if ext == '.pdf':
        return "📕"
    elif ext in ['.docx']:
        return "📘"
    elif ext in ['.xlsx', '.xls', '.xlsm']:
        return "📊"
    else:
        return "📄"