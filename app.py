import streamlit as st
from utils.pdf_reader import extract_pdf_text
from utils.docx_reader import extract_docx_text, create_translated_docx
from utils.translator import translate_text, detect_language
from utils.file_utils import allowed_file_type

st.set_page_config(page_title="Universal Document Translator", layout="wide")

# ---------------------------------------------------------
# Dark Mode / Pro UI CSS
# ---------------------------------------------------------
st.markdown("""
<style>
body {
    background-color: #1e1e1e;
    color: #e6e6e6;
}
.block-container {
    padding-top: 2rem;
}
.card {
    background: #2a2a2a;
    padding: 30px;
    border-radius: 15px;
    border: 1px solid #3a3a3a;
}
.upload-box {
    border: 2px dashed #555;
    border-radius: 15px;
    padding: 35px;
    text-align: center;
    color: #bbb;
    background-color: #252525;
}
.translate-btn {
    background: linear-gradient(to right, #6b9bff, #996bff);
    color: white !important;
    padding: 15px 20px;
    border-radius: 10px;
    text-align: center;
    font-size: 18px;
    border: none;
}
</style>
""", unsafe_allow_html=True)

# ==========================================================
#                  PAGE TITLE
# ==========================================================
st.markdown("<h1 style='text-align:center;'>🌐 Universal Document Translator</h1>", unsafe_allow_html=True)
st.caption("AI-powered translation for PDF & DOCX files • Auto-detect language • Error‑safe")

# ==========================================================
#                  DOCUMENT TRANSLATOR
# ==========================================================
st.markdown("<div class='card'>", unsafe_allow_html=True)
st.subheader("📄 Document Translator")

uploaded = st.file_uploader("Upload PDF or DOCX file", type=["pdf", "docx"])

auto_detect_enabled = st.checkbox("Auto-detect source language", value=True)

col1, col2 = st.columns(2)
with col1:
    source_lang = st.text_input("Source Language (ISO code)", "auto")
with col2:
    target_lang = st.selectbox("Target Language", ["en", "es", "fr", "de", "zh", "ar", "it"])

output_filename = st.text_input("Output filename (without extension)", "translated_output")

translate_doc = st.button("🔁 Translate Document", type="primary", help="Translate the uploaded file")

st.markdown("</div>", unsafe_allow_html=True)

# ==========================================================
#           PROCESS DOCUMENT TRANSLATION WITH ERRORS
# ==========================================================
if translate_doc:
    if not uploaded:
        st.error("❌ No file uploaded.")
    else:
        if not allowed_file_type(uploaded):
            st.error("❌ Unsupported file type. Only PDF and DOCX allowed.")
        else:
            # Extract text safely
            if uploaded.name.endswith(".pdf"):
                text = extract_pdf_text(uploaded)
            else:
                text = extract_docx_text(uploaded)

            if not text or text.strip() == "":
                st.error("❌ Could not read text from the document. It may be scanned, encrypted, or corrupted.")
            else:
                # Auto-detect language
                if auto_detect_enabled:
                    detected = detect_language(text)
                    if detected:
                        source_lang = detected
                        st.info(f"🌍 Auto-detected source language: **{detected}**")
                    else:
                        st.warning("⚠️ Auto-detection failed. Using manual source language.")

                # Translate safely
                translated = translate_text(text, source_lang, target_lang)

                if not translated:
                    st.error("❌ Translation failed. Unsupported language or connection error.")
                else:
                    st.success("✅ Translation completed successfully!")

                    buffer = create_translated_docx(translated)
                    st.download_button(
                        label="📥 Download Translated File",
                        data=buffer,
                        file_name=f"{output_filename}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )

# ==========================================================
#                  TEXT TRANSLATOR
# ==========================================================
st.markdown("<div class='card'>", unsafe_allow_html=True)
st.subheader("✏️ Text-to-Text Translator")

colA, colB = st.columns(2)
with colA:
    input_text = st.text_area("Input Text")

with colB:
    output_text = st.text_area("Translated Output", disabled=True)

colC, colD = st.columns(2)
with colC:
    clear = st.button("Clear")
with colD:
    submit = st.button("Translate Text")

if clear:
    st.experimental_rerun()

if submit:
    if not input_text.strip():
        st.error("❌ Please enter text.")
    else:
        # Auto detect
        if auto_detect_enabled:
            detected = detect_language(input_text)
            if detected:
                source_lang = detected
                st.info(f"Detected language: **{source_lang}**")
            else:
                st.warning("Could not auto-detect language.")

        translated = translate_text(input_text, source_lang, target_lang)
        if translated:
            st.text_area("Translated Output", translated)
        else:
            st.error("❌ Translation failed.")

st.markdown("</div>", unsafe_allow_html=True)