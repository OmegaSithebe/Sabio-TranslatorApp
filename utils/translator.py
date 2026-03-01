from deep_translator import GoogleTranslator
from langdetect import detect, DetectorFactory
DetectorFactory.seed = 0  # consistency

def detect_language(text):
    try:
        return detect(text)
    except Exception:
        return None

def translate_text(text, source, target):
    try:
        translated = GoogleTranslator(source=source, target=target).translate(text)
        return translated
    except Exception:
        return None