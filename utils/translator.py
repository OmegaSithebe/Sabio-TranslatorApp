# utils/translator.py
from deep_translator import GoogleTranslator
from langdetect import detect, DetectorFactory, LangDetectException
import time
from typing import Optional, Tuple
import streamlit as st

# Ensure consistent language detection
DetectorFactory.seed = 42

# Comprehensive language mapping
LANGUAGE_MAP = {
    'en': 'English',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'it': 'Italian',
    'pt': 'Portuguese',
    'nl': 'Dutch',
    'ru': 'Russian',
    'zh-cn': 'Chinese (Simplified)',
    'zh-tw': 'Chinese (Traditional)',
    'ja': 'Japanese',
    'ko': 'Korean',
    'ar': 'Arabic',
    'hi': 'Hindi',
    'tr': 'Turkish',
    'pl': 'Polish',
    'uk': 'Ukrainian',
    'vi': 'Vietnamese',
    'th': 'Thai',
    'cs': 'Czech',
    'el': 'Greek',
    'sv': 'Swedish',
    'da': 'Danish',
    'fi': 'Finnish',
    'no': 'Norwegian',
    'hu': 'Hungarian',
    'ro': 'Romanian',
    'bg': 'Bulgarian',
    'id': 'Indonesian',
    'ms': 'Malay'
}

def detect_language(text: str) -> Optional[str]:
    """
    Safely detect language with improved error handling
    
    Args:
        text: Text to detect language from
        
    Returns:
        ISO language code or None if detection fails
    """
    if not text or len(text.strip()) < 10:
        return None
    
    try:
        # Clean text for better detection
        clean_text = ' '.join(text.split()[:100])  # First 100 words usually enough
        lang = detect(clean_text)
        
        # Map zh-cn/zh-tw to zh for Google Translate compatibility
        if lang.startswith('zh'):
            return 'zh'
        
        return lang if lang in LANGUAGE_MAP else None
        
    except LangDetectException:
        return None
    except Exception as e:
        st.warning(f"Language detection issue: {str(e)}")
        return None

def translate_text(text: str, source: str, target: str, max_retries: int = 2) -> Optional[str]:
    """
    Translate text with retry logic and chunking for large texts
    
    Args:
        text: Text to translate
        source: Source language code
        target: Target language code
        max_retries: Number of retry attempts
        
    Returns:
        Translated text or None if translation fails
    """
    if not text or not text.strip():
        return ""
    
    # Handle auto-detection
    if source == "auto":
        detected = detect_language(text)
        if detected:
            source = detected
        else:
            source = "en"  # Default to English
    
    # Ensure language codes are valid
    source = source.split('-')[0]  # Remove region if present
    target = target.split('-')[0]
    
    # Split text into chunks if too long (Google Translate has limits)
    max_chunk_size = 4500  # Safe limit below 5000
    chunks = [text[i:i + max_chunk_size] for i in range(0, len(text), max_chunk_size)]
    
    translated_chunks = []
    
    for i, chunk in enumerate(chunks):
        for attempt in range(max_retries):
            try:
                translator = GoogleTranslator(source=source, target=target)
                translated = translator.translate(chunk)
                
                if translated:
                    translated_chunks.append(translated)
                    break
                else:
                    if attempt < max_retries - 1:
                        time.sleep(1)  # Wait before retry
                    else:
                        translated_chunks.append(chunk)  # Keep original if all retries fail
                        
            except Exception as e:
                if "429" in str(e):  # Rate limit
                    time.sleep(2)  # Wait longer for rate limits
                elif attempt < max_retries - 1:
                    time.sleep(1)
                else:
                    # On final failure, append original chunk
                    translated_chunks.append(chunk)
                    st.warning(f"Chunk {i+1} translation failed, keeping original")
    
    return ' '.join(translated_chunks)

def get_language_name(code: str) -> str:
    """Get readable language name from code"""
    return LANGUAGE_MAP.get(code, code)

def is_language_supported(code: str) -> bool:
    """Check if language is supported"""
    return code in LANGUAGE_MAP