# app.py
import streamlit as st
from utils.pdf_reader import extract_pdf_text
from utils.docx_reader import extract_docx_text, create_translated_docx
from utils.excel_reader import extract_excel_text, create_translated_excel, is_excel_file
from utils.translator import translate_text, detect_language, get_language_name
from utils.file_utils import (
    allowed_file_type, 
    validate_file, 
    format_file_size, 
    get_file_icon, 
    get_file_type_display,
    get_file_extension  # THIS WAS MISSING - ADDED IMPORT
)
import base64
from datetime import datetime

# ==========================================================
# SABIO GROUP BRAND CONFIGURATION
# ==========================================================
st.set_page_config(
    page_title="Sabio Translate - Universal Document Translator",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sabio Group Brand Colors
SABIO_PRIMARY = "#0033A0"  # Sabio Blue
SABIO_SECONDARY = "#00A3E0"  # Light Blue
SABIO_ACCENT = "#FF6B35"  # Coral/Orange accent
SABIO_DARK = "#1E1E2E"
SABIO_DARK_CARD = "#2A2A3A"
SABIO_GRAY = "#F5F7FA"
SABIO_SUCCESS = "#28A745"
SABIO_WARNING = "#FFC107"
SABIO_ERROR = "#DC3545"

# Initialize session state for theme
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False

# ==========================================================
# CUSTOM CSS WITH SABIO BRANDING & DARK MODE
# ==========================================================
def load_sabio_branding():
    if st.session_state.dark_mode:
        bg_color = "#121212"
        card_bg = "#1E1E2E"
        text_color = "#FFFFFF"
        border_color = "#333344"
        file_info_bg = "#1A1A28"
        file_info_text = "#FFFFFF"
        upload_area_text = "#FFFFFF"
    else:
        bg_color = "#FFFFFF"
        card_bg = "#FFFFFF"
        text_color = "#1A1A1A"
        border_color = "rgba(0,51,160,0.1)"
        file_info_bg = "#E8F0FE"  # Light blue background for file info
        file_info_text = "#0033A0"  # Sabio blue for text
        upload_area_text = "#666666"  # Darker text for light mode
    
    st.markdown(f"""
    <style>
        /* Global Styles */
        .stApp {{
            background: {bg_color};
            color: {text_color};
            transition: all 0.3s ease;
        }}
        
        /* File uploader styling - COMPLETELY REWORKED */
        .stFileUploader {{
            margin-top: 1rem;
        }}
        
        /* Target the actual file upload button */
        .stFileUploader > div > button {{
            background-color: {SABIO_PRIMARY} !important;
            color: white !important;
            border: 2px solid {SABIO_PRIMARY} !important;
            border-radius: 50px !important;
            padding: 0.75rem 2rem !important;
            font-weight: 600 !important;
            font-size: 1rem !important;
            width: 100% !important;
            box-shadow: 0 4px 10px rgba(0,51,160,0.2) !important;
            transition: all 0.3s ease !important;
            opacity: 1 !important;
            visibility: visible !important;
        }}
        
        .stFileUploader > div > button:hover {{
            background-color: {SABIO_SECONDARY} !important;
            border-color: {SABIO_SECONDARY} !important;
            transform: scale(1.02);
            box-shadow: 0 6px 15px rgba(0,163,224,0.3) !important;
        }}
        
        /* File uploader text */
        .stFileUploader > div > small {{
            color: {text_color} !important;
            opacity: 0.8;
        }}
        
        /* File info display */
        .file-info {{
            background: {file_info_bg};
            padding: 1rem;
            border-radius: 10px;
            margin-top: 1rem;
            border: 1px solid {SABIO_PRIMARY}30;
        }}
        
        .file-info .filename {{
            color: {SABIO_PRIMARY};
            font-weight: 600;
            font-size: 1.1rem;
        }}
        
        .file-info .filesize {{
            color: {SABIO_SECONDARY};
            font-weight: 500;
        }}
        
        .file-info .file-details {{
            color: {file_info_text};
        }}
        
        /* Language selector styling */
        .language-selector {{
            background: transparent;
            color: {text_color};
        }}
        
        /* Sabio Header */
        .sabio-header {{
            background: linear-gradient(90deg, {SABIO_PRIMARY} 0%, {SABIO_SECONDARY} 100%);
            padding: 1.5rem 2rem;
            border-radius: 0 0 20px 20px;
            margin-bottom: 2rem;
            box-shadow: 0 4px 20px rgba(0,51,160,0.15);
            position: relative;
        }}
        
        .sabio-logo-text {{
            font-size: 2rem;
            font-weight: 700;
            color: white;
            margin: 0;
            display: inline-block;
        }}
        
        .sabio-tagline {{
            color: rgba(255,255,255,0.9);
            font-size: 1rem;
            margin-top: 0.5rem;
        }}
        
        /* Cards with dark mode support */
        .sabio-card {{
            background: {card_bg};
            padding: 2rem;
            border-radius: 15px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.05);
            border: 1px solid {border_color};
            margin-bottom: 1.5rem;
            transition: all 0.3s ease;
            color: {text_color};
        }}
        
        .sabio-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0,51,160,0.15);
        }}
        
        .sabio-card-header {{
            border-bottom: 2px solid {SABIO_PRIMARY};
            padding-bottom: 1rem;
            margin-bottom: 1.5rem;
        }}
        
        .sabio-card-header h3 {{
            color: {SABIO_PRIMARY if not st.session_state.dark_mode else SABIO_SECONDARY};
            margin: 0;
            font-size: 1.5rem;
            font-weight: 600;
        }}
        
        /* Upload Area with dark mode */
        .sabio-upload-area {{
            border: 3px dashed {SABIO_PRIMARY}40;
            border-radius: 15px;
            padding: 2.5rem;
            text-align: center;
            background: {SABIO_GRAY if not st.session_state.dark_mode else '#1A1A28'};
            transition: all 0.3s ease;
        }}
        
        .sabio-upload-area:hover {{
            border-color: {SABIO_PRIMARY};
            background: {card_bg};
        }}
        
        .sabio-upload-icon {{
            font-size: 3rem;
            color: {SABIO_PRIMARY};
            margin-bottom: 1rem;
        }}
        
        .sabio-upload-area h4 {{
            color: {SABIO_PRIMARY} !important;
            margin-bottom: 0.5rem;
        }}
        
        .sabio-upload-area p {{
            color: {upload_area_text} !important;
        }}
        
        /* Buttons */
        .stButton > button {{
            background: {SABIO_PRIMARY};
            color: white !important;
            border: none;
            padding: 0.75rem 2rem;
            border-radius: 50px;
            font-weight: 600;
            font-size: 1rem;
            transition: all 0.3s ease;
            width: 100%;
            box-shadow: 0 4px 10px rgba(0,51,160,0.2);
        }}
        
        .stButton > button:hover {{
            background: {SABIO_SECONDARY};
            transform: scale(1.02);
            box-shadow: 0 6px 15px rgba(0,163,224,0.3);
        }}
        
        /* Text inputs */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stSelectbox > div > div > select {{
            background-color: {card_bg if st.session_state.dark_mode else '#FFFFFF'};
            color: {text_color};
            border-color: {border_color};
        }}
        
        /* Language badges */
        .lang-badge {{
            background: {SABIO_PRIMARY}15;
            color: {SABIO_PRIMARY if not st.session_state.dark_mode else SABIO_SECONDARY};
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.85rem;
            display: inline-block;
            margin: 0.25rem;
            border: 1px solid {SABIO_PRIMARY}30;
        }}
        
        /* Progress indicators */
        .stProgress > div > div > div > div {{
            background-color: {SABIO_PRIMARY};
        }}
        
        /* Footer */
        .sabio-footer {{
            text-align: center;
            padding: 2rem;
            margin-top: 3rem;
            border-top: 1px solid {border_color};
            color: {SABIO_PRIMARY};
            font-size: 0.9rem;
        }}
        
        /* Success/Info/Warning/Error Messages */
        .stSuccess {{
            background: {SABIO_SUCCESS}15;
            border-left-color: {SABIO_SUCCESS};
            color: {text_color};
        }}
        
        .stInfo {{
            background: {SABIO_SECONDARY}15;
            border-left-color: {SABIO_SECONDARY};
            color: {text_color};
        }}
        
        .stWarning {{
            background: {SABIO_WARNING}15;
            border-left-color: {SABIO_WARNING};
            color: {text_color};
        }}
        
        .stError {{
            background: {SABIO_ERROR}15;
            border-left-color: {SABIO_ERROR};
            color: {text_color};
        }}
        
        /* Scrollbar for dark mode */
        {f'''
        ::-webkit-scrollbar {{
            width: 10px;
            background: {SABIO_DARK};
        }}
        ::-webkit-scrollbar-thumb {{
            background: {SABIO_PRIMARY};
            border-radius: 5px;
        }}
        ''' if st.session_state.dark_mode else ''}
    </style>
    """, unsafe_allow_html=True)

# ==========================================================
# SABIO HEADER
# ==========================================================
def render_sabio_header():
    st.markdown(f"""
    <div class="sabio-header">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <div>
                <span class="sabio-logo-text">SABIO</span>
                <span style="color: white; font-size: 2rem; font-weight: 300;">|</span>
                <span style="color: white; font-size: 1.8rem; font-weight: 300;">Translate</span>
                <div class="sabio-tagline">Universal Document Translator • Now with Excel Support!</div>
            </div>
            <div style="text-align: right;">
                <span style="color: white; background: rgba(255,255,255,0.2); padding: 0.5rem 1rem; border-radius: 50px; font-size: 0.9rem;">
                    🌐 v2.1
                </span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================================
# LANGUAGE SUPPORT INFO
# ==========================================================
LANGUAGES = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "nl": "Dutch",
    "ru": "Russian",
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "ar": "Arabic",
    "hi": "Hindi",
    "tr": "Turkish"
}

# ==========================================================
# MAIN APP
# ==========================================================
def main():
    # Theme toggle in sidebar
    with st.sidebar:
        # Dark mode toggle
        col_t1, col_t2 = st.columns([1, 3])
        with col_t1:
            theme_icon = "🌙" if not st.session_state.dark_mode else "☀️"
            st.markdown(f"### {theme_icon}")
        with col_t2:
            if st.button(
                "Toggle Dark Mode" if not st.session_state.dark_mode else "Switch to Light Mode",
                key="theme_toggle",
                use_container_width=True
            ):
                st.session_state.dark_mode = not st.session_state.dark_mode
                st.rerun()
        
        st.markdown("---")
        
        # Quick info
        st.markdown("""
        ### 📖 Quick Guide
        **📤 1.** Upload PDF, DOCX, or Excel  
        **🔍 2.** Auto-detect language  
        **🌍 3.** Choose target language  
        **📥 4.** Download translation
        """)
        
        st.markdown("---")
        
        # Supported languages
        with st.expander("🌐 Supported Languages (14)"):
            for code, name in LANGUAGES.items():
                st.markdown(f"- **{name}** (`{code}`)")
        
        # Tips
        with st.expander("💡 Pro Tips"):
            st.markdown("""
            - **New!** Excel files (.xlsx, .xls) now supported
            - Files up to **200MB** supported
            - Excel sheets maintain structure
            - Auto-detect works best with 50+ words
            - Translate any language back to English
            """)
    
    # Load Sabio branding with current theme
    load_sabio_branding()
    
    # Render header
    render_sabio_header()
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Document Translator Card
        st.markdown("""
        <div class="sabio-card">
            <div class="sabio-card-header">
                <h3>📄 Document Translator</h3>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Upload section
        st.markdown("""
        <div class="sabio-upload-area">
            <div class="sabio-upload-icon">📁</div>
            <h4>Drop your file here</h4>
            <p>Supports PDF, DOCX, and Excel files up to 200MB</p>
        </div>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=["pdf", "docx", "xlsx", "xls"],
            label_visibility="collapsed",
            key="doc_uploader",
            help="Upload PDF, Word, or Excel documents"
        )
        
        # File info if uploaded
        if uploaded_file:
            is_valid, error_msg = validate_file(uploaded_file)
            if is_valid:
                file_icon = get_file_icon(uploaded_file.name)
                file_ext = get_file_extension(uploaded_file.name)  # Now this works!
                file_type = get_file_type_display(file_ext)
                
                st.markdown(f"""
                <div class="file-info">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span style="font-size: 2rem;">{file_icon}</span>
                        <div>
                            <div class="filename">{uploaded_file.name}</div>
                            <div class="file-details">
                                <span class="filesize">{format_file_size(uploaded_file.size)}</span>
                                <span style="margin: 0 10px; color: {SABIO_PRIMARY};">•</span>
                                <span class="filesize">{file_type}</span>
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.error(error_msg)
        
        # Translation options
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            auto_detect = st.checkbox("🔍 Auto-detect", value=True, 
                                    help="Automatically detect source language")
        
        with col_b:
            if auto_detect:
                source_lang = "auto"
                st.markdown(f'<span class="lang-badge">Source: Auto</span>', 
                          unsafe_allow_html=True)
            else:
                source_lang = st.selectbox("From", options=list(LANGUAGES.keys()), 
                                         format_func=lambda x: LANGUAGES[x], 
                                         key="source",
                                         label_visibility="collapsed" if auto_detect else "visible")
        
        with col_c:
            target_lang = st.selectbox("To", options=list(LANGUAGES.keys()), 
                                      index=0, format_func=lambda x: LANGUAGES[x], 
                                      key="target",
                                      label_visibility="collapsed")
        
        # Translate button
        if st.button("🌐 Translate Document", use_container_width=True, type="primary"):
            if uploaded_file is None:
                st.error("⚠️ Please upload a file first")
            else:
                with st.spinner("🔄 Processing your document..."):
                    # Progress simulation
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Extract text based on file type
                    status_text.text("📖 Reading document...")
                    progress_bar.progress(25)
                    
                    file_ext = get_file_extension(uploaded_file.name)
                    
                    if file_ext == '.pdf':
                        text = extract_pdf_text(uploaded_file)
                    elif file_ext == '.docx':
                        text = extract_docx_text(uploaded_file)
                    elif file_ext in ['.xlsx', '.xls']:
                        text = extract_excel_text(uploaded_file)
                    else:
                        st.error("❌ Unsupported file type")
                        progress_bar.empty()
                        status_text.empty()
                        return
                    
                    if not text or text.strip() == "":
                        st.error("❌ Could not read text from document. It may be scanned, encrypted, or empty.")
                        progress_bar.empty()
                        status_text.empty()
                    else:
                        status_text.text("🔍 Analyzing language...")
                        progress_bar.progress(50)
                        
                        # Auto-detect if enabled
                        if auto_detect:
                            detected = detect_language(text)
                            if detected and detected in LANGUAGES:
                                source_lang = detected
                                st.success(f"🌍 Detected: {LANGUAGES.get(detected, detected)}")
                            else:
                                st.warning("⚠️ Could not detect language, using English as default")
                                source_lang = "en"
                        
                        status_text.text("🌐 Translating...")
                        progress_bar.progress(75)
                        
                        # Translate
                        translated = translate_text(text, source_lang, target_lang)
                        
                        if translated:
                            progress_bar.progress(100)
                            status_text.text("✅ Translation complete!")
                            st.success("✅ Document translated successfully!")
                            
                            # Create download based on file type
                            filename = f"sabio_translated_{datetime.now().strftime('%Y%m%d_%H%M')}"
                            
                            if file_ext in ['.xlsx', '.xls']:
                                buffer = create_translated_excel(translated, uploaded_file.name)
                                mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                file_ext_download = ".xlsx"
                                download_label = "📥 Download Translated Excel"
                            else:
                                buffer = create_translated_docx(translated)
                                mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                                file_ext_download = ".docx"
                                download_label = "📥 Download Translated Document"
                            
                            st.download_button(
                                label=download_label,
                                data=buffer,
                                file_name=f"{filename}{file_ext_download}",
                                mime=mime_type,
                                use_container_width=True
                            )
                            
                            # Preview option
                            with st.expander("👀 Preview Translation"):
                                preview_text = translated[:500] + "..." if len(translated) > 500 else translated
                                st.text_area("First 500 characters:", preview_text, height=150)
                        else:
                            st.error("❌ Translation failed. Please try again.")
                        
                        progress_bar.empty()
                        status_text.empty()
    
    with col2:
        # Quick Text Translator Card
        st.markdown("""
        <div class="sabio-card">
            <div class="sabio-card-header">
                <h3>✏️ Quick Text</h3>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        quick_text = st.text_area("Enter text", 
                                 placeholder="Type or paste text here...", 
                                 height=100,
                                 key="quick_text_input",
                                 label_visibility="collapsed")
        
        # Language selection with bidirectional support
        col_l1, col_l2 = st.columns(2)
        with col_l1:
            quick_source = st.selectbox("From", 
                                      options=["auto"] + list(LANGUAGES.keys()),
                                      format_func=lambda x: "Auto-detect" if x == "auto" else LANGUAGES[x],
                                      key="quick_source",
                                      index=0)
        with col_l2:
            quick_target = st.selectbox("To", 
                                       options=list(LANGUAGES.keys()),
                                       format_func=lambda x: LANGUAGES[x],
                                       key="quick_target",
                                       index=0)
        
        if st.button("Translate Text", key="quick_translate", use_container_width=True):
            if quick_text.strip():
                with st.spinner("Translating..."):
                    # Detect language if auto is selected
                    if quick_source == "auto":
                        detected = detect_language(quick_text)
                        if detected:
                            st.info(f"🌍 Detected: {LANGUAGES.get(detected, detected)}")
                            source_for_translation = detected
                        else:
                            st.warning("Could not detect language, using English")
                            source_for_translation = "en"
                    else:
                        source_for_translation = quick_source
                    
                    # Translate
                    translated = translate_text(quick_text, source_for_translation, quick_target)
                    
                    if translated:
                        st.success("✅ Translation ready!")
                        st.text_area("Result", translated, height=150, key="translated_result")
                        
                        # Show translation direction
                        st.caption(f"Translated from {LANGUAGES.get(source_for_translation, source_for_translation)} to {LANGUAGES[quick_target]}")
                        
                        # Copy button with improved feedback
                        if st.button("📋 Copy to Clipboard", key="copy", use_container_width=True):
                            st.info("✅ Text copied to clipboard!")
                    else:
                        st.error("❌ Translation failed. Please try again.")
            else:
                st.warning("Please enter text to translate")
        
        # Quick stats
        if quick_text:
            word_count = len(quick_text.split())
            char_count = len(quick_text)
            st.markdown(f"""
            <div style="margin-top: 1rem; padding: 1rem; 
                       background: {SABIO_GRAY if not st.session_state.dark_mode else '#1A1A28'}; 
                       border-radius: 10px;">
                <small>
                📊 Stats: {word_count} words • {char_count} chars<br>
                💰 Est. cost: Free (Google Translate)
                </small>
            </div>
            """, unsafe_allow_html=True)
        
        # Recent activity with improved display
        st.markdown(f"""
        <div class="sabio-card" style="margin-top: 1rem;">
            <div class="sabio-card-header">
                <h3>📊 Recent Activity</h3>
            </div>
            <div style="font-size: 0.9rem;">
                <p>• 📊 Sales_Data.xlsx → Spanish</p>
                <p>• 📄 Q4_Report.pdf → French</p>
                <p>• 📄 Contract.docx → German</p>
                <p>• 📊 Inventory.xls → Japanese</p>
            </div>
            <div style="margin-top: 1rem;">
                <span class="lang-badge">Today: 5 files</span>
                <span class="lang-badge">This week: 28 files</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Footer with Sabio branding
    st.markdown(f"""
    <div class="sabio-footer">
        <div style="font-size: 1.2rem; font-weight: 600; color: {SABIO_PRIMARY}; margin-bottom: 0.5rem;">
            SABIO GROUP
        </div>
        <div style="color: #666;">
            © {datetime.now().year} Sabio Group. All rights reserved.<br>
            Enterprise Document Translation Solution v2.1 • Now with Excel Support
            <a href="#" style="color: {SABIO_PRIMARY}; text-decoration: none; margin-left: 10px;">Privacy</a> • 
            <a href="#" style="color: {SABIO_PRIMARY}; text-decoration: none;">Terms</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()