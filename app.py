"""
app.py — Sabio Translate
Universal Document Translator that preserves all formatting, images,
logos, tables, and layout.  Only the text changes.
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
    page_title = "Sabio Translate",
    layout     = "wide",
    initial_sidebar_state = "expanded",
)

# ── Brand tokens ───────────────────────────────────────────────────────────
PRIMARY   = "#0033A0"
SECONDARY = "#00A3E0"
LIGHT_BG  = "#EEF2FB"

# ── Session state ──────────────────────────────────────────────────────────
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False


# ══════════════════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════════════════

def _css() -> None:
    dm = st.session_state.dark_mode
    bg       = "#0D0D1A"   if dm else "#FFFFFF"
    surface  = "#1A1A2E"   if dm else "#F5F7FA"
    card     = "#1E1E30"   if dm else "#FFFFFF"
    text     = "#F0F0FF"   if dm else "#1A1A2E"
    muted    = "#8888AA"   if dm else "#6B7280"
    border   = "rgba(255,255,255,0.07)" if dm else "rgba(0,51,160,0.10)"
    inp      = "#252538"   if dm else "#FFFFFF"
    plab     = SECONDARY   if dm else PRIMARY

    st.markdown(f"""
    <style>
    .stApp {{
        background: {bg};
        color: {text};
        font-family: "Inter","Segoe UI",system-ui,sans-serif;
    }}
    /* Header */
    .app-header {{
        background: linear-gradient(100deg, {PRIMARY} 0%, {SECONDARY} 100%);
        padding: 1.4rem 2.4rem;
        border-radius: 0 0 16px 16px;
        margin-bottom: 1.8rem;
        box-shadow: 0 4px 24px rgba(0,51,160,0.18);
    }}
    .app-header h1 {{
        color:#fff; font-size:1.85rem; font-weight:700;
        margin:0; letter-spacing:-.3px;
    }}
    .app-header p {{
        color:rgba(255,255,255,.82); margin:.3rem 0 0; font-size:.9rem;
    }}
    .ver-badge {{
        background:rgba(255,255,255,.18); color:#fff;
        padding:.28rem .85rem; border-radius:20px; font-size:.8rem;
    }}
    /* Cards */
    .card {{
        background:{card}; border:1px solid {border};
        border-radius:13px; padding:1.6rem;
        margin-bottom:1.4rem;
        box-shadow:0 2px 10px rgba(0,0,0,.05);
    }}
    .card-title {{
        color:{plab}; font-size:1.08rem; font-weight:600;
        border-bottom:2px solid {PRIMARY}20;
        padding-bottom:.65rem; margin-bottom:1.1rem;
    }}
    /* Upload zone */
    .upload-zone {{
        border:2px dashed {PRIMARY}50; border-radius:11px;
        padding:1.8rem; text-align:center;
        background:{"#1A1A2E" if dm else LIGHT_BG};
        margin-bottom:.9rem;
    }}
    .upload-zone p {{ color:{muted}; margin:0; font-size:.88rem; }}
    .upload-zone strong {{ color:{plab}; font-size:1rem; }}
    /* File strip */
    .file-strip {{
        background:{"#252538" if dm else LIGHT_BG};
        border:1px solid {PRIMARY}22; border-radius:9px;
        padding:.8rem 1rem; margin:.6rem 0 1.1rem;
        display:flex; align-items:center; gap:.9rem;
    }}
    .file-strip .badge {{
        background:{PRIMARY}; color:#fff;
        font-size:.7rem; font-weight:700;
        padding:.18rem .5rem; border-radius:5px; letter-spacing:.4px;
    }}
    .file-strip .fname {{ color:{plab}; font-weight:600; font-size:.96rem; }}
    .file-strip .fmeta {{ color:{muted}; font-size:.83rem; }}
    /* Info box */
    .info-box {{
        background:{"#1A2A3A" if dm else "#E8F4FD"};
        border-left:3px solid {SECONDARY};
        border-radius:0 8px 8px 0;
        padding:.7rem 1rem; margin:.6rem 0;
        font-size:.88rem; color:{text};
    }}
    /* Buttons */
    .stButton > button {{
        background:{PRIMARY}; color:#fff !important;
        border:none; padding:.6rem 1.4rem;
        border-radius:8px; font-weight:600; font-size:.93rem;
        width:100%; transition:background .2s,transform .15s;
        box-shadow:0 2px 8px rgba(0,51,160,.2);
    }}
    .stButton > button:hover {{
        background:{SECONDARY}; transform:translateY(-1px);
    }}
    /* Inputs */
    .stTextInput > div > div > input,
    .stTextArea  > div > div > textarea,
    .stSelectbox > div > div {{
        background:{inp} !important; color:{text} !important;
        border-color:{border} !important; border-radius:8px !important;
    }}
    /* Progress */
    .stProgress > div > div > div > div {{ background:{PRIMARY}; }}
    /* Sidebar */
    section[data-testid="stSidebar"] {{
        background:{surface}; border-right:1px solid {border};
    }}
    section[data-testid="stSidebar"] * {{ color:{text} !important; }}
    /* Footer */
    .footer {{
        text-align:center; padding:1.8rem 1rem 1rem;
        margin-top:1.8rem; border-top:1px solid {border};
        color:{muted}; font-size:.83rem;
    }}
    .footer a {{ color:{plab}; text-decoration:none; }}
    {"" if not dm else f"""
    ::-webkit-scrollbar {{ width:7px; background:#0D0D1A; }}
    ::-webkit-scrollbar-thumb {{ background:{PRIMARY}; border-radius:4px; }}
    """}
    </style>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════
# Layout helpers
# ══════════════════════════════════════════════════════════════════════════

def _header():
    st.markdown("""
    <div class="app-header">
      <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:.8rem;">
        <div>
          <h1>SABIO &nbsp;|&nbsp; Translate</h1>
          <p>Layout-preserving document translation — PDF, Word, and Excel</p>
        </div>
        <span class="ver-badge">v3.0</span>
      </div>
    </div>""", unsafe_allow_html=True)


def _sidebar():
    with st.sidebar:
        label = "Switch to Light Mode" if st.session_state.dark_mode else "Switch to Dark Mode"
        if st.button(label, use_container_width=True):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()

        st.divider()
        st.markdown("#### How it works")
        st.markdown(
            "1. Upload a PDF, DOCX, or XLSX file  \n"
            "2. Source language is detected automatically  \n"
            "3. Choose a target language  \n"
            "4. Download the translated file — logos, tables, and "
            "formatting are preserved exactly"
        )
        st.divider()
        st.markdown(
            '<div class="info-box" style="border-left-color:#0033A0">'
            "<strong>What is preserved?</strong><br>"
            "Images &amp; logos &nbsp;·&nbsp; Table borders &amp; shading &nbsp;·&nbsp; "
            "Fonts &amp; colours &nbsp;·&nbsp; Headers &amp; footers &nbsp;·&nbsp; "
            "Merged cells &nbsp;·&nbsp; Charts"
            "</div>",
            unsafe_allow_html=True,
        )
        st.divider()
        with st.expander("Supported languages"):
            for code, name in SUPPORTED_LANGUAGES.items():
                st.markdown(f"- **{name}** `{code}`")


# ══════════════════════════════════════════════════════════════════════════
# Document translator panel
# ══════════════════════════════════════════════════════════════════════════

def _doc_panel():
    st.markdown('<div class="card"><div class="card-title">Document Translator</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="upload-zone">
        <strong>Select or drop a file</strong>
        <p>PDF · DOCX · XLSX &nbsp;—&nbsp; up to 200 MB</p>
    </div>""", unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "file", type=["pdf", "docx", "xlsx"],
        label_visibility="collapsed", key="doc_up",
    )

    if uploaded:
        ok, msg = validate_file(uploaded)
        if not ok:
            st.error(msg)
            st.markdown("</div>", unsafe_allow_html=True)
            return

        ext   = get_file_extension(uploaded.name)
        badge = get_file_icon(uploaded.name)
        st.markdown(f"""
        <div class="file-strip">
          <span class="badge">{badge}</span>
          <div>
            <div class="fname">{uploaded.name}</div>
            <div class="fmeta">{format_file_size(uploaded.size)} &nbsp;·&nbsp;
                               {get_file_type_display(ext)}</div>
          </div>
        </div>""", unsafe_allow_html=True)

    col_a, col_b, col_c = st.columns([1, 1, 1])
    with col_a:
        auto = st.checkbox("Auto-detect source language", value=True)
    with col_b:
        if auto:
            src = "auto"
            st.caption("Source: Auto-detect")
        else:
            src = st.selectbox(
                "Source language",
                list(SUPPORTED_LANGUAGES.keys()),
                format_func=lambda c: SUPPORTED_LANGUAGES[c],
                key="doc_src",
            )
    with col_c:
        tgt = st.selectbox(
            "Target language",
            list(SUPPORTED_LANGUAGES.keys()),
            format_func=lambda c: SUPPORTED_LANGUAGES[c],
            key="doc_tgt",
            index=0,   # English first
        )

    if st.button("Translate Document", use_container_width=True):
        if uploaded is None:
            st.warning("Please upload a file before translating.")
        else:
            _run(uploaded, src, tgt)

    st.markdown("</div>", unsafe_allow_html=True)


# ── Core translation runner ────────────────────────────────────────────────

def _run(uploaded, src: str, tgt: str):
    progress = st.progress(0)
    status   = st.empty()

    try:
        ext = get_file_extension(uploaded.name)

        # 1 ── Extract text for language detection
        status.text("Reading document...")
        progress.progress(15)
        uploaded.seek(0)

        if ext == ".pdf":
            sample_text = extract_pdf_text(uploaded)
        elif ext == ".docx":
            sample_text = extract_docx_text(uploaded)
        elif ext == ".xlsx":
            sample_text = extract_excel_text(uploaded)
        else:
            st.error(f"Unsupported file type: {ext}")
            return

        if not sample_text or not sample_text.strip():
            st.error(
                "No readable text was found.  The file may be scanned, "
                "encrypted, or empty."
            )
            return

        # 2 ── Detect source language
        status.text("Detecting language...")
        progress.progress(30)

        if src == "auto":
            detected = detect_language(sample_text)
            if detected:
                src = detected
                st.info(f"Detected language: {get_language_name(detected)}")
            else:
                src = "en"
                st.warning("Language could not be detected — defaulting to English.")

        if src == tgt:
            st.warning("Source and target languages are the same — nothing to translate.")
            return

        # 3 ── Build translate callables bound to src/tgt
        progress.progress(40)

        def _translate_one(text: str) -> str:
            """Single-string fallback (used for OCR and Quick Text)."""
            if not text or not text.strip():
                return text
            return translate_text(text, src, tgt) or text

        def _translate_batch(strings: list[str]) -> dict[str, str]:
            """
            Fast path: batch + parallel translation of many strings at once.
            Returns dict mapping original → translated.
            """
            return translate_many(strings, src, tgt)

        # 4 ── Translate in-place (batch mode)
        status.text("Translating — batching requests for speed...")
        progress.progress(55)
        uploaded.seek(0)

        if ext == ".pdf":
            out_buf = translate_pdf_inplace(uploaded, _translate_one,
                                            translate_many_fn=_translate_batch)
            mime    = "application/pdf"
            dl_ext  = ".pdf"
            dl_lbl  = "Download Translated PDF"

        elif ext == ".docx":
            out_buf = translate_docx_inplace(uploaded, _translate_one,
                                             translate_many_fn=_translate_batch)
            mime    = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            dl_ext  = ".docx"
            dl_lbl  = "Download Translated Word Document"

        elif ext == ".xlsx":
            out_buf = translate_xlsx_inplace(uploaded, _translate_one,
                                             translate_many_fn=_translate_batch)
            mime    = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            dl_ext  = ".xlsx"
            dl_lbl  = "Download Translated Excel File"

        progress.progress(95)

        if out_buf is None:
            st.error("Translation failed.  Check the warnings above for details.")
            return

        progress.progress(100)
        status.text("Complete.")
        st.success("Translation complete.  All formatting, images, and tables are preserved.")

        ts = datetime.now().strftime("%Y%m%d_%H%M")
        st.download_button(
            label     = dl_lbl,
            data      = out_buf,
            file_name = f"sabio_translated_{ts}{dl_ext}",
            mime      = mime,
            use_container_width=True,
        )

    finally:
        progress.empty()
        status.empty()


# ══════════════════════════════════════════════════════════════════════════
# Quick Text panel
# ══════════════════════════════════════════════════════════════════════════

def _text_panel():
    st.markdown('<div class="card"><div class="card-title">Quick Text Translator</div>', unsafe_allow_html=True)

    text_in = st.text_area(
        "Text", placeholder="Paste or type text here...",
        height=120, key="qt_in", label_visibility="collapsed",
    )

    c1, c2 = st.columns(2)
    with c1:
        qs = st.selectbox(
            "From",
            ["auto"] + list(SUPPORTED_LANGUAGES.keys()),
            format_func=lambda c: "Auto-detect" if c == "auto" else SUPPORTED_LANGUAGES[c],
            key="qt_src",
        )
    with c2:
        qt = st.selectbox(
            "To",
            list(SUPPORTED_LANGUAGES.keys()),
            format_func=lambda c: SUPPORTED_LANGUAGES[c],
            key="qt_tgt",
            index=0,
        )

    if st.button("Translate Text", key="qt_btn", use_container_width=True):
        if not text_in.strip():
            st.warning("Please enter some text.")
        else:
            with st.spinner("Translating..."):
                s = qs
                if qs == "auto":
                    det = detect_language(text_in)
                    if det:
                        st.info(f"Detected: {get_language_name(det)}")
                        s = det
                    else:
                        s = "en"
                result = translate_text(text_in, s, qt)
            if result:
                st.success("Done.")
                st.text_area("Result", result, height=160, key="qt_out")
                st.caption(f"{get_language_name(s)} → {get_language_name(qt)}")
            else:
                st.error("Translation failed.")

    if text_in:
        st.caption(f"{len(text_in.split())} words · {len(text_in)} characters")

    st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════
# Entry point
# ══════════════════════════════════════════════════════════════════════════

def main():
    _sidebar()
    _css()
    _header()

    col_l, col_r = st.columns([2, 1])
    with col_l:
        _doc_panel()
    with col_r:
        _text_panel()

    st.markdown(
        f'<div class="footer">'
        f'<strong style="color:{PRIMARY};font-size:.95rem;">SABIO GROUP</strong><br>'
        f'&copy; {datetime.now().year} Sabio Group. All rights reserved. &nbsp;|&nbsp; '
        f'Enterprise Document Translation &nbsp;·&nbsp; v3.0 &nbsp;·&nbsp; '
        f'<a href="#">Privacy</a> &nbsp;·&nbsp; <a href="#">Terms</a>'
        f'</div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
