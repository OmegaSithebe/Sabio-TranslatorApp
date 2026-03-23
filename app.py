"""
app.py — Sabio Translate
Single-Page Universal Document Translator
"""

from datetime import datetime
import streamlit as st

from utils.pdf_reader   import extract_pdf_text, translate_pdf_inplace
from utils.docx_reader  import extract_docx_text, translate_docx_inplace
from utils.excel_reader import extract_excel_text, translate_xlsx_inplace
from utils.translator   import (
    translate_text,
    translate_many,
    detect_language,
    get_language_name,
    SUPPORTED_LANGUAGES,
)
from utils.file_utils import (
    validate_file,
    format_file_size,
    get_file_icon,
    get_file_type_display,
    get_file_extension,
)

# ── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Sabio Translate",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Brand tokens ───────────────────────────────────────────────────────────
PRIMARY = "#0066CC"
SECONDARY = "#00A3E0"

# ── Session state ──────────────────────────────────────────────────────────
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False
if "show_languages" not in st.session_state:
    st.session_state.show_languages = False


# ══════════════════════════════════════════════════════════════════════════
# CSS - Clean, Single Page Layout
# ══════════════════════════════════════════════════════════════════════════

def _css() -> None:
    dm = st.session_state.dark_mode
    
    if dm:
        bg_color = "#0A0A0F"
        text_color = "#FFFFFF"
        secondary_text = "#CCCCCC"
        card_bg = "#15151F"
        border = "rgba(255,255,255,0.1)"
    else:
        bg_color = "#F5F7FB"
        text_color = "#1A1A2E"
        secondary_text = "#6B7280"
        card_bg = "#FFFFFF"
        border = "rgba(0,0,0,0.1)"
    
    st.markdown(f"""
    <style>
    /* Hide default Streamlit padding */
    .main .block-container {{
        padding-top: 1rem;
        padding-bottom: 0rem;
        max-width: 1400px;
    }}
    
    /* Header */
    .app-header {{
        background: linear-gradient(135deg, {PRIMARY}, {SECONDARY});
        padding: 1rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        color: white;
    }}
    
    .app-header h1 {{
        margin: 0;
        font-size: 1.8rem;
        font-weight: 700;
    }}
    
    .app-header p {{
        margin: 0.25rem 0 0;
        opacity: 0.9;
        font-size: 0.85rem;
    }}
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {{
        background-color: {card_bg};
        border-right: 1px solid {border};
    }}
    
    /* Sidebar content - scrollable only when needed */
    .sidebar-section {{
        margin-bottom: 1.5rem;
    }}
    
    .sidebar-title {{
        font-weight: 600;
        font-size: 1rem;
        margin-bottom: 0.75rem;
        color: {PRIMARY};
        border-bottom: 2px solid {PRIMARY};
        display: inline-block;
        padding-bottom: 0.25rem;
    }}
    
    .step-item {{
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin: 0.5rem 0;
        color: {secondary_text};
        font-size: 0.85rem;
    }}
    
    .step-number {{
        background: {PRIMARY};
        color: white;
        width: 22px;
        height: 22px;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 0.7rem;
        font-weight: bold;
    }}
    
    .feature-tag {{
        display: inline-block;
        background: {PRIMARY}15;
        color: {PRIMARY};
        padding: 0.2rem 0.6rem;
        border-radius: 20px;
        font-size: 0.7rem;
        margin: 0.2rem;
    }}
    
    /* Language List - Scrollable Container */
    .language-scroll {{
        max-height: 300px;
        overflow-y: auto;
        margin-top: 0.5rem;
        padding-right: 0.5rem;
    }}
    
    .language-scroll::-webkit-scrollbar {{
        width: 4px;
    }}
    
    .language-scroll::-webkit-scrollbar-track {{
        background: {border};
        border-radius: 4px;
    }}
    
    .language-scroll::-webkit-scrollbar-thumb {{
        background: {PRIMARY};
        border-radius: 4px;
    }}
    
    .lang-item {{
        padding: 0.3rem 0.5rem;
        font-size: 0.8rem;
        color: {secondary_text};
        border-radius: 6px;
    }}
    
    .lang-item:hover {{
        background: {PRIMARY}10;
        color: {PRIMARY};
    }}
    
    .lang-code {{
        color: {PRIMARY};
        font-size: 0.7rem;
        margin-left: 0.5rem;
    }}
    
    /* Main Content Card */
    .main-card {{
        background: {card_bg};
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid {border};
        margin-bottom: 1rem;
    }}
    
    /* Upload Zone */
    .upload-zone {{
        border: 2px dashed {PRIMARY}40;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        background: {PRIMARY}05;
        margin-bottom: 1rem;
    }}
    
    /* File Info */
    .file-info {{
        background: {PRIMARY}10;
        border-radius: 10px;
        padding: 0.75rem;
        margin: 1rem 0;
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }}
    
    .file-badge {{
        background: {PRIMARY};
        color: white;
        padding: 0.2rem 0.6rem;
        border-radius: 20px;
        font-size: 0.7rem;
        font-weight: 600;
    }}
    
    .file-name {{
        font-weight: 500;
        font-size: 0.85rem;
        flex: 1;
    }}
    
    /* Footer */
    .footer {{
        text-align: center;
        padding: 1rem;
        color: {secondary_text};
        font-size: 0.7rem;
        border-top: 1px solid {border};
        margin-top: 1rem;
    }}
    
    /* Dark Mode Toggle */
    .dark-toggle {{
        position: fixed;
        bottom: 1rem;
        right: 1rem;
        z-index: 999;
        background: {card_bg};
        border: 1px solid {border};
        border-radius: 50px;
        padding: 0.3rem 0.8rem;
        font-size: 0.8rem;
        cursor: pointer;
    }}
    
    /* Responsive */
    @media (max-width: 768px) {{
        .main .block-container {{
            padding: 0.5rem;
        }}
        .main-card {{
            padding: 1rem;
        }}
        .upload-zone {{
            padding: 1rem;
        }}
    }}
    </style>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════
# Sidebar Content
# ══════════════════════════════════════════════════════════════════════════

def _sidebar():
    with st.sidebar:
        # Brand
        st.markdown("""
        <div style="text-align: center; margin-bottom: 1.5rem;">
            <h1 style="font-size: 1.8rem; margin: 0; background: linear-gradient(135deg, #0066CC, #00A3E0); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">SABIO</h1>
            <p style="margin: 0; font-size: 0.8rem; opacity: 0.7;">Enterprise Translation</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Instructions
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-title">📖 How to Use</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="step-item">
            <span class="step-number">1</span>
            <span>Upload your document</span>
        </div>
        <div class="step-item">
            <span class="step-number">2</span>
            <span>Select languages</span>
        </div>
        <div class="step-item">
            <span class="step-number">3</span>
            <span>Click Translate</span>
        </div>
        <div class="step-item">
            <span class="step-number">4</span>
            <span>Download result</span>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Supported Languages Button
        if st.button("🌍 Supported Languages", use_container_width=True, key="lang_btn"):
            st.session_state.show_languages = not st.session_state.show_languages
        
        # Language List - Only this scrolls
        if st.session_state.show_languages:
            st.markdown('<div class="language-scroll">', unsafe_allow_html=True)
            for code, name in SUPPORTED_LANGUAGES.items():
                st.markdown(f"""
                <div class="lang-item">
                    {name}
                    <span class="lang-code">{code}</span>
                </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Features
        st.markdown('<div class="sidebar-section" style="margin-top: 1rem;">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-title">✨ Features</div>', unsafe_allow_html=True)
        st.markdown("""
        <div>
            <span class="feature-tag">Preserves formatting</span>
            <span class="feature-tag">Images & logos</span>
            <span class="feature-tag">Tables & charts</span>
            <span class="feature-tag">Headers & footers</span>
            <span class="feature-tag">25+ languages</span>
            <span class="feature-tag">Batch translation</span>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Dark Mode Toggle
        dm = st.session_state.dark_mode
        toggle_label = "🌙 Dark Mode" if not dm else "☀️ Light Mode"
        if st.button(toggle_label, use_container_width=True):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════
# Main Content
# ══════════════════════════════════════════════════════════════════════════

def _main_content():
    # Header
    st.markdown("""
    <div class="app-header">
        <h1>Document Translator</h1>
        <p>Translate your documents while preserving all original formatting</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Main Card
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    
    # Upload Zone
    st.markdown("""
    <div class="upload-zone">
        <div style="font-size: 2rem;">📄</div>
        <div><strong>Upload your document</strong></div>
        <div style="font-size: 0.8rem; opacity: 0.7;">PDF · DOCX · XLSX · Up to 200 MB</div>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded = st.file_uploader(
        "",
        type=["pdf", "docx", "xlsx"],
        label_visibility="collapsed",
        key="doc_upload"
    )
    
    # File info if uploaded
    if uploaded:
        ext = get_file_extension(uploaded.name)
        badge = get_file_icon(uploaded.name)
        st.markdown(f"""
        <div class="file-info">
            <span class="file-badge">{badge}</span>
            <span class="file-name">{uploaded.name}</span>
            <span style="font-size: 0.7rem; opacity: 0.6;">{format_file_size(uploaded.size)}</span>
        </div>
        """, unsafe_allow_html=True)
    
    # Language Selection
    col1, col2 = st.columns(2)
    
    with col1:
        auto_detect = st.checkbox("Auto-detect source language", value=True)
        if auto_detect:
            source_lang = "auto"
            st.caption("✨ Language will be detected automatically")
        else:
            source_lang = st.selectbox(
                "Source Language",
                list(SUPPORTED_LANGUAGES.keys()),
                format_func=lambda x: SUPPORTED_LANGUAGES[x],
                key="src_lang"
            )
    
    with col2:
        target_lang = st.selectbox(
            "Target Language",
            list(SUPPORTED_LANGUAGES.keys()),
            format_func=lambda x: SUPPORTED_LANGUAGES[x],
            index=0,
            key="tgt_lang"
        )
    
    # Translate Button
    if st.button("🚀 Translate Document", use_container_width=True, key="translate_btn"):
        if uploaded is None:
            st.error("❌ Please upload a document first")
        else:
            _run_translation(uploaded, source_lang, target_lang, auto_detect)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer
    st.markdown(f"""
    <div class="footer">
        <strong>SABIO GROUP</strong> — Enterprise Document Translation<br>
        © {datetime.now().year} Sabio Group. All rights reserved.
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════
# Translation Runner
# ══════════════════════════════════════════════════════════════════════════

def _run_translation(uploaded, source_lang, target_lang, auto_detect):
    with st.spinner("Processing..."):
        try:
            ext = get_file_extension(uploaded.name)
            uploaded.seek(0)
            
            # Extract text for detection
            if ext == ".pdf":
                sample_text = extract_pdf_text(uploaded)
            elif ext == ".docx":
                sample_text = extract_docx_text(uploaded)
            elif ext == ".xlsx":
                sample_text = extract_excel_text(uploaded)
            else:
                st.error("Unsupported file type")
                return
            
            if not sample_text or not sample_text.strip():
                st.error("No readable text found in the document")
                return
            
            # Detect language if auto
            if auto_detect:
                detected = detect_language(sample_text)
                if detected:
                    source_lang = detected
                    st.success(f"✅ Detected: {get_language_name(detected)}")
                else:
                    source_lang = "en"
                    st.warning("⚠️ Could not detect language, defaulting to English")
            
            if source_lang == target_lang:
                st.warning("⚠️ Source and target languages are the same")
                return
            
            # Translation functions
            def _translate_one(text):
                return translate_text(text, source_lang, target_lang) or text
            
            def _translate_batch(strings):
                return translate_many(strings, source_lang, target_lang)
            
            # Translate
            uploaded.seek(0)
            
            if ext == ".pdf":
                out = translate_pdf_inplace(uploaded, _translate_one, translate_many_fn=_translate_batch)
                mime = "application/pdf"
                dl_ext = ".pdf"
            elif ext == ".docx":
                out = translate_docx_inplace(uploaded, _translate_one, translate_many_fn=_translate_batch)
                mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                dl_ext = ".docx"
            elif ext == ".xlsx":
                out = translate_xlsx_inplace(uploaded, _translate_one, translate_many_fn=_translate_batch)
                mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                dl_ext = ".xlsx"
            else:
                out = None
            
            if out:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M")
                st.success("🎉 Translation complete! All formatting preserved.")
                st.download_button(
                    label="📥 Download Translated Document",
                    data=out,
                    file_name=f"sabio_translated_{timestamp}{dl_ext}",
                    mime=mime,
                    use_container_width=True,
                )
            else:
                st.error("❌ Translation failed. Please check the document and try again.")
                
        except Exception as e:
            st.error(f"Error: {str(e)}")


# ══════════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════════

def main():
    _css()
    _sidebar()
    _main_content()


if __name__ == "__main__":
    main()