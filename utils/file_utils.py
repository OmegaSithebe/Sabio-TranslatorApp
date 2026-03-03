# utils/file_utils.py
import os
from typing import Tuple, Optional
import streamlit as st

# File size limits (in bytes)
MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB
ALLOWED_EXTENSIONS = {'.pdf', '.docx'}

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
        return False, f"File type not supported: {get_file_extension(file.name)}"
    
    return True, "File valid"

def format_file_size(size_in_bytes: int) -> str:
    """Format file size for display"""
    if size_in_bytes < 1024:
        return f"{size_in_bytes} B"
    elif size_in_bytes < 1024 * 1024:
        return f"{size_in_bytes / 1024:.1f} KB"
    else:
        return f"{size_in_bytes / (1024 * 1024):.1f} MB"