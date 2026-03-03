# app.py
import streamlit as st
from utils.pdf_reader import extract_pdf_text
from utils.docx_reader import extract_docx_text, create_translated_docx
from utils.translator import translate_text, detect_language
from utils.file_utils import allowed_file_type, validate_file, format_file_size
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
    else:
        bg_color = "#FFFFFF"
        card_bg = "#FFFFFF"
        text_color = "#1A1A1A"
        border_color = "rgba(0,51,160,0.1)"
    
    st.markdown(f"""
    <style>
        /* Global Styles */
        .stApp {{
            background: {bg_color};
            color: {text_color};
            transition: all 0.3s ease;
        }}
        
        /* Theme Toggle Button */
        .theme-toggle {{
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 999;
            background: {SABIO_PRIMARY};
            color: white;
            border: none;
            border-radius: 50px;
            padding: 10px 20px;
            font-size: 14px;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(0,51,160,0.3);
            transition: all 0.3s ease;
        }}
        
        .theme-toggle:hover {{
            transform: scale(1.05);
            background: {SABIO_SECONDARY};
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
            color: {text_color};
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
        
        /* Buttons with dark mode support */
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
        
        /* Secondary button for dark mode toggle */
        .stButton > button.secondary {{
            background: transparent;
            border: 2px solid {SABIO_PRIMARY};
            color: {SABIO_PRIMARY} !important;
            box-shadow: none;
        }}
        
        .stButton > button.secondary:hover {{
            background: {SABIO_PRIMARY}10;
            transform: scale(1.02);
        }}
        
        /* Text inputs with dark mode */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stSelectbox > div > div > select {{
            background-color: {card_bg if st.session_state.dark_mode else '#FFFFFF'};
            color: {text_color};
            border-color: {border_color};
        }}
        
        /* Language badges with dark mode */
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
        
        /* Sidebar with dark mode */
        .css-1d391kg, .css-1wrcr25 {{
            background-color: {card_bg};
        }}
        
        /* Footer with dark mode */
        .sabio-footer {{
            text-align: center;
            padding: 2rem;
            margin-top: 3rem;
            border-top: 1px solid {border_color};
            color: {SABIO_PRIMARY};
            font-size: 0.9rem;
        }}
        
        /* Success/Info/Warning/Error Messages with dark mode */
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
    
    <!-- Theme Toggle Button -->
    <div class="theme-toggle" onclick="toggleTheme()">
        {"🌙 Dark Mode" if not st.session_state.dark_mode else "☀️ Light Mode"}
    </div>
    
    <script>
    function toggleTheme() {{
        // This will be handled by Streamlit
        window.parent.postMessage({{
            type: 'streamlit:setComponentValue',
            value: {str(not st.session_state.dark_mode).lower()}
        }}, '*');
    }}
    </script>
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
                <div class="sabio-tagline">Universal Document Translator • Powered by AI</div>
            </div>
            <div style="text-align: right;">
                <span style="color: white; background: rgba(255,255,255,0.2); padding: 0.5rem 1rem; border-radius: 50px; font-size: 0.9rem;">
                    🌐 v2.0
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
        **📤 1.** Upload PDF or DOCX  
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
            - Files up to **200MB** supported
            - **OCR** not supported yet
            - Keep formatting in DOCX
            - Auto-detect works best with 50+ words
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
            <h4 style="color: #0033A0;">Drop your file here</h4>
            <p style="color: #666;">Supports PDF and DOCX up to 200MB</p>
        </div>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=["pdf", "docx"],
            label_visibility="collapsed",
            key="doc_uploader"
        )
        
        # File info if uploaded
        if uploaded_file:
            is_valid, error_msg = validate_file(uploaded_file)
            if is_valid:
                st.markdown(f"""
                <div style="background: {SABIO_GRAY if not st.session_state.dark_mode else '#1A1A28'}; 
                           padding: 1rem; border-radius: 10px; margin-top: 1rem;">
                    <span class="lang-badge">📎 {uploaded_file.name}</span>
                    <span class="lang-badge">📊 {format_file_size(uploaded_file.size)}</span>
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
                    
                    # Extract text
                    status_text.text("📖 Reading document...")
                    progress_bar.progress(25)
                    
                    if uploaded_file.name.endswith(".pdf"):
                        text = extract_pdf_text(uploaded_file)
                    else:
                        text = extract_docx_text(uploaded_file)
                    
                    if not text or text.strip() == "":
                        st.error("❌ Could not read text from document. It may be scanned or encrypted.")
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
                            
                            # Create download button
                            buffer = create_translated_docx(translated)
                            filename = f"sabio_translated_{datetime.now().strftime('%Y%m%d_%H%M')}"
                            
                            st.download_button(
                                label="📥 Download Translated Document",
                                data=buffer,
                                file_name=f"{filename}.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
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
                                 label_visibility="collapsed")
        
        quick_target = st.selectbox("Translate to", 
                                   options=list(LANGUAGES.keys())[:5], 
                                   format_func=lambda x: LANGUAGES[x], 
                                   key="quick_target",
                                   label_visibility="collapsed")
        
        if st.button("Translate", key="quick_translate", use_container_width=True):
            if quick_text.strip():
                with st.spinner("Translating..."):
                    detected = detect_language(quick_text)
                    if detected:
                        st.caption(f"Detected: {LANGUAGES.get(detected, detected)}")
                    
                    translated = translate_text(quick_text, "auto", quick_target)
                    if translated:
                        st.success("Translation ready!")
                        st.text_area("Result", translated, height=100)
                        
                        # Copy button (simulated)
                        if st.button("📋 Copy to Clipboard", key="copy", use_container_width=True):
                            st.info("Text copied! (simulated - clipboard access requires JavaScript)")
                    else:
                        st.error("Translation failed")
            else:
                st.warning("Please enter text")
        
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
        
        # Recent activity with dark mode support
        st.markdown(f"""
        <div class="sabio-card" style="margin-top: 1rem;">
            <div class="sabio-card-header">
                <h3>📊 Recent Activity</h3>
            </div>
            <div style="font-size: 0.9rem;">
                <p>• 📄 Q4_Report.pdf → Spanish</p>
                <p>• 📄 Contract.docx → French</p>
                <p>• 📄 Manual.pdf → German</p>
                <p>• 📄 Presentation.pptx → Japanese</p>
            </div>
            <div style="margin-top: 1rem;">
                <span class="lang-badge">Today: 4 files</span>
                <span class="lang-badge">This week: 23 files</span>
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
            Enterprise Document Translation Solution v2.0 • 
            <a href="#" style="color: {SABIO_PRIMARY}; text-decoration: none;">Privacy</a> • 
            <a href="#" style="color: {SABIO_PRIMARY}; text-decoration: none;">Terms</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()