"""
app.py – Streamlit UI for the AI Text Summarizer with Multi-Engine & Live Streaming.

Run with:
    python -m streamlit run app.py

Features:
    - AI Engine Selector: Groq Ultra-Fast vs NVIDIA Nemotron 3 Ultra
    - Real-time Token Streaming via st.write_stream
    - Document Upload (.pdf, .docx, .txt) with fallback to manual paste
    - Multi-format Export: PDF, DOCX, Markdown, Copy, Clear
    - White + Cyan ClubFlux-inspired theme
"""

import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

import summarizer
import utils
import exporters

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Text Summarizer",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS – White + Cyan Theme
# ---------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Audiowide&family=Raleway:wght@300;400;500;600;700;800&family=Share+Tech+Mono&display=swap');

/* ── GLOBAL BASE ── */
html, body, .stApp {
    background-color: #f0fafb !important;
    color: #0e1117 !important;
    font-family: 'Raleway', sans-serif !important;
}

/* ── SIDEBAR ── */
section[data-testid="stSidebar"] {
    background-color: #ffffff !important;
    border-right: 2px solid #06b6d4 !important;
}
section[data-testid="stSidebar"] * {
    color: #1e293b !important;
    font-family: 'Raleway', sans-serif !important;
}
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    font-family: 'Audiowide', monospace !important;
    color: #0891b2 !important;
    font-size: 0.78rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
}

/* ── SIDEBAR RADIO PILLS ── */
[data-testid="stRadio"] label {
    background: #f0fafb !important;
    border: 1px solid #bae6fd !important;
    border-radius: 8px !important;
    color: #475569 !important;
    padding: 6px 12px !important;
    margin-bottom: 3px !important;
    transition: all 0.2s ease !important;
    font-size: 0.88rem !important;
}
[data-testid="stRadio"] label:hover {
    background: #e0f7fa !important;
    border-color: #06b6d4 !important;
    color: #0891b2 !important;
}
[data-testid="stRadio"] [aria-checked="true"] + div label,
[data-testid="stRadio"] label[data-checked="true"] {
    background: #cffafe !important;
    border-color: #06b6d4 !important;
    color: #0e7490 !important;
}

/* ── TEXT AREA ── */
.stTextArea textarea {
    background-color: #ffffff !important;
    color: #1e293b !important;
    border: 1.5px solid #bae6fd !important;
    border-radius: 10px !important;
    font-family: 'Raleway', sans-serif !important;
    font-size: 0.95rem !important;
    line-height: 1.7 !important;
}
.stTextArea textarea:focus {
    border-color: #06b6d4 !important;
    box-shadow: 0 0 0 3px rgba(6, 182, 212, 0.15) !important;
}
.stTextArea textarea::placeholder {
    color: #94a3b8 !important;
}

/* ── TABS ── */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 2px solid #bae6fd !important;
    gap: 4px !important;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    background: #f0fafb !important;
    border: 1px solid #bae6fd !important;
    border-bottom: none !important;
    border-radius: 8px 8px 0 0 !important;
    color: #64748b !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.82rem !important;
    letter-spacing: 0.04em !important;
    padding: 0.4rem 1.2rem !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    background: #cffafe !important;
    color: #0891b2 !important;
    border-color: #06b6d4 !important;
    font-weight: 600 !important;
}

/* ── PRIMARY BUTTON (Summarize) ── */
.stButton > button {
    background: linear-gradient(135deg, #06b6d4, #0891b2) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Audiowide', monospace !important;
    font-size: 0.88rem !important;
    letter-spacing: 0.06em !important;
    padding: 0.6rem 2rem !important;
    box-shadow: 0 4px 20px rgba(6, 182, 212, 0.35) !important;
    transition: all 0.25s ease !important;
    width: 100% !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #22d3ee, #06b6d4) !important;
    box-shadow: 0 6px 28px rgba(6, 182, 212, 0.5) !important;
    transform: translateY(-2px) !important;
}
.stButton > button:active {
    transform: translateY(0px) !important;
}

/* ── DOWNLOAD BUTTONS ── */
[data-testid="stDownloadButton"] > button {
    background: #ffffff !important;
    color: #0891b2 !important;
    border: 1.5px solid #06b6d4 !important;
    border-radius: 8px !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.8rem !important;
    letter-spacing: 0.03em !important;
    transition: all 0.2s ease !important;
}
[data-testid="stDownloadButton"] > button:hover {
    background: #cffafe !important;
    box-shadow: 0 3px 12px rgba(6, 182, 212, 0.25) !important;
    transform: translateY(-1px) !important;
}

/* ── METRICS ── */
[data-testid="stMetric"] {
    background: #ffffff !important;
    border: 1.5px solid #bae6fd !important;
    border-top: 3px solid #06b6d4 !important;
    border-radius: 10px !important;
    padding: 1rem !important;
}
[data-testid="stMetricValue"] {
    color: #0891b2 !important;
    font-family: 'Audiowide', monospace !important;
    font-size: 1.5rem !important;
}
[data-testid="stMetricLabel"] {
    color: #64748b !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.72rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
}

/* ── STATUS WIDGET ── */
[data-testid="stStatus"] {
    background: #ffffff !important;
    border: 1px solid #bae6fd !important;
    border-radius: 10px !important;
    color: #1e293b !important;
}

/* ── ALERTS ── */
[data-testid="stAlert"] {
    border-radius: 8px !important;
    font-family: 'Raleway', sans-serif !important;
}

/* ── EXPANDER ── */
[data-testid="stExpander"] {
    background: #ffffff !important;
    border: 1px solid #bae6fd !important;
    border-radius: 8px !important;
}
[data-testid="stExpander"] summary {
    color: #0891b2 !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.85rem !important;
}

/* ── FILE UPLOADER ── */
[data-testid="stFileUploader"] {
    background: #ffffff !important;
    border: 1.5px dashed #06b6d4 !important;
    border-radius: 10px !important;
}

/* ── TEXT INPUT (API key) ── */
[data-testid="stTextInput"] input {
    background: #ffffff !important;
    border: 1px solid #bae6fd !important;
    border-radius: 8px !important;
    color: #1e293b !important;
    font-family: 'Share Tech Mono', monospace !important;
}
[data-testid="stTextInput"] input:focus {
    border-color: #06b6d4 !important;
    box-shadow: 0 0 0 3px rgba(6, 182, 212, 0.15) !important;
}

/* ── HR ── */
hr {
    border: none !important;
    height: 2px !important;
    background: linear-gradient(90deg, transparent, #06b6d4, transparent) !important;
    margin: 1.2rem 0 !important;
}

/* ── CAPTION ── */
[data-testid="stCaptionContainer"], .stCaption {
    color: #64748b !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.75rem !important;
}

/* ── CODE ── */
code, pre {
    background: #f0fafb !important;
    border: 1px solid #bae6fd !important;
    border-radius: 6px !important;
    color: #0891b2 !important;
    font-family: 'Share Tech Mono', monospace !important;
}

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #f0fafb; }
::-webkit-scrollbar-thumb { background: #06b6d4; border-radius: 10px; }

/* ── CUSTOM COMPONENT STYLES ── */
.cyber-title {
    font-family: 'Audiowide', monospace;
    font-size: 2.2rem;
    color: #0891b2;
    letter-spacing: 0.06em;
    line-height: 1.2;
}
.cyber-subtitle {
    font-family: 'Share Tech Mono', monospace;
    color: #94a3b8;
    font-size: 0.85rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-top: 0.2rem;
}
.cyber-divider {
    height: 2px;
    background: linear-gradient(90deg, #06b6d4, #22d3ee, #06b6d4);
    border-radius: 2px;
    margin: 1rem 0;
}
.cyber-badge {
    display: inline-block;
    background: #cffafe;
    border: 1px solid #06b6d4;
    border-radius: 4px;
    padding: 3px 10px;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.75rem;
    color: #0891b2;
    letter-spacing: 0.06em;
    margin-right: 6px;
    font-weight: 600;
}
.engine-badge {
    display: inline-block;
    background: #ede9fe;
    border: 1px solid #8b5cf6;
    border-radius: 4px;
    padding: 3px 12px;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.75rem;
    color: #7c3aed;
    letter-spacing: 0.06em;
    margin-left: 10px;
    vertical-align: middle;
}
.summary-box {
    background: #ffffff;
    border: 1.5px solid #06b6d4;
    border-radius: 12px;
    padding: 1.6rem 2rem;
    line-height: 1.85;
    color: #1e293b;
    font-size: 0.96rem;
    font-family: 'Raleway', sans-serif;
    white-space: pre-wrap;
    box-shadow: 0 4px 24px rgba(6, 182, 212, 0.1);
    position: relative;
}
.summary-box::before {
    content: '[ SUMMARY OUTPUT ]';
    position: absolute;
    top: -11px;
    left: 20px;
    background: #ffffff;
    padding: 0 8px;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.68rem;
    color: #06b6d4;
    letter-spacing: 0.1em;
    font-weight: 600;
}
.file-badge {
    background: #cffafe;
    border: 1px solid #06b6d4;
    border-radius: 6px;
    padding: 0.4rem 0.9rem;
    color: #0891b2;
    font-size: 0.83rem;
    font-family: 'Share Tech Mono', monospace;
    margin-bottom: 0.6rem;
    display: inline-block;
}
.export-label {
    color: #64748b;
    font-size: 0.7rem;
    font-family: 'Share Tech Mono', monospace;
    text-align: center;
    margin-bottom: 0.3rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}
.section-header {
    font-family: 'Audiowide', monospace;
    font-size: 0.82rem;
    color: #0891b2;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 0.5rem;
}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## ⚡ AI CONFIG")
    st.markdown("---")

    st.markdown("### 🤖 AI Engine")
    has_groq_key = bool(os.environ.get("GROQ_API_KEY", "").strip())
    engine_choice = st.radio(
        label="AI Engine",
        options=["⚡ Groq Ultra-Fast (Sub-second)", "🧠 NVIDIA Nemotron 3 Ultra (550B)"],
        index=0 if has_groq_key else 1,
        help="Groq delivers instant sub-second summaries. NVIDIA Nemotron uses a massive 550B parameter model.",
        label_visibility="collapsed",
    )
    engine_key = "groq" if "Groq" in engine_choice else "nvidia"

    custom_groq_key = None
    if engine_key == "groq" and not has_groq_key:
        st.info("💡 **Groq is 100% Free & 10x faster!** Get your key at [console.groq.com](https://console.groq.com)")
        custom_groq_key = st.text_input(
            "Groq API Key", type="password", placeholder="gsk_...",
            help="Paste your Groq API key here"
        )

    st.markdown("---")
    st.markdown("### 📐 Output Mode")
    output_mode = st.radio(
        label="Output Mode",
        options=["Bullet Points", "Short Paragraph"],
        index=0,
        label_visibility="collapsed",
    )
    mode_key = "bullet" if output_mode == "Bullet Points" else "paragraph"

    st.markdown("---")
    st.markdown("### 📏 Summary Length")
    length_choice = st.radio(
        label="Summary Length",
        options=["Short", "Medium", "Detailed"],
        index=1,
        label_visibility="collapsed",
    )
    length_key = length_choice.lower()

    st.markdown("---")
    st.markdown("### 🎯 Audience Style")
    style_choice = st.radio(
        label="Audience Style",
        options=["Student Notes", "Executive Brief", "Simple (ELI5)"],
        index=0,
        label_visibility="collapsed",
    )
    style_map = {"Student Notes": "student", "Executive Brief": "executive", "Simple (ELI5)": "eli5"}
    style_key = style_map[style_choice]

    st.markdown("---")
    st.markdown(
        '<div style="font-family:\'Share Tech Mono\',monospace;font-size:0.68rem;'
        'color:#94a3b8;text-align:center;letter-spacing:0.05em;padding:0.4rem 0;">'
        'AI TEXT SUMMARIZER v2.0<br>POWERED BY NVIDIA &amp; GROQ'
        '</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Main – Hero Header
# ---------------------------------------------------------------------------
st.markdown(
    '<div class="cyber-title">AI TEXT SUMMARIZER</div>'
    '<div class="cyber-subtitle">// Neural Compression Engine &nbsp;·&nbsp; Multi-Model &nbsp;·&nbsp; Live Streaming</div>',
    unsafe_allow_html=True,
)
st.markdown('<div class="cyber-divider"></div>', unsafe_allow_html=True)

st.markdown(
    '<span class="cyber-badge">GROQ LPU</span>'
    '<span class="cyber-badge">NVIDIA NIM</span>'
    '<span class="cyber-badge">REAL-TIME STREAM</span>',
    unsafe_allow_html=True,
)
st.markdown("")


# ---------------------------------------------------------------------------
# Input Section
# ---------------------------------------------------------------------------
tab_paste, tab_upload = st.tabs(["[ PASTE TEXT ]", "[ UPLOAD FILE ]"])

with tab_paste:
    pasted_text = st.text_area(
        label="Input Text",
        placeholder="Paste your text here (minimum 30 words)...",
        height=240,
        label_visibility="collapsed",
        key="paste_area",
    )

with tab_upload:
    uploaded_file = st.file_uploader(
        "Upload document",
        type=["txt", "pdf", "docx"],
        label_visibility="collapsed",
        key="file_uploader",
    )
    if uploaded_file is not None:
        extracted, err = utils.extract_text_from_file(uploaded_file)
        if err:
            st.error(f"⚠️ {err}")
        else:
            st.session_state["uploaded_text"] = extracted
            st.session_state["uploaded_name"] = uploaded_file.name
            st.success(f"✅ Loaded **{uploaded_file.name}** — {utils.count_words(extracted):,} words detected")

# Determine active text
upload_text   = st.session_state.get("uploaded_text", "")
upload_source = st.session_state.get("uploaded_name", None)

if upload_text and not pasted_text.strip():
    input_text = upload_text
    st.markdown(
        f'<div class="file-badge">📁 Document: <strong>{upload_source}</strong>'
        f'&nbsp;|&nbsp; {utils.count_words(input_text):,} words</div>',
        unsafe_allow_html=True,
    )
else:
    input_text    = pasted_text
    upload_source = None

raw_words = utils.count_words(input_text)
if raw_words > 0:
    st.caption(f"Word count: {raw_words:,} words")

st.markdown("")
summarize_clicked = st.button(
    "⚡  INITIALIZE SUMMARIZATION",
    use_container_width=True,
    key="summarize_btn",
)


# ---------------------------------------------------------------------------
# Summarization + Streaming
# ---------------------------------------------------------------------------
if summarize_clicked:
    cleaned = utils.clean_text(input_text)
    is_valid, error_msg = utils.validate_input(cleaned)

    if not is_valid:
        st.warning(error_msg)
    else:
        st.markdown('<div class="cyber-divider"></div>', unsafe_allow_html=True)
        engine_label = summarizer.ENGINES[engine_key]["name"]
        status_box   = st.status(f"⚡ Connecting to {engine_label}...", expanded=True)

        def on_status(msg: str):
            status_box.write(f"› {msg}")

        try:
            stream_gen, chunks_used = summarizer.stream_summarize(
                text=cleaned,
                mode=mode_key,
                length=length_key,
                style=style_key,
                engine=engine_key,
                custom_key=custom_groq_key,
                status_callback=on_status,
            )
            status_box.update(label="⚡ Streaming summary...", state="running", expanded=False)

            st.markdown(
                f'<div class="section-header">[ LIVE OUTPUT ] &nbsp;'
                f'<span style="font-size:0.7rem;color:#94a3b8;font-family:\'Share Tech Mono\',monospace;">'
                f'via {engine_label}</span></div>',
                unsafe_allow_html=True,
            )
            stream_container = st.empty()
            full_summary     = stream_container.write_stream(stream_gen)
            status_box.update(label="✅ Summary ready!", state="complete", expanded=False)

            st.session_state["summary"]       = full_summary
            st.session_state["chunks_used"]   = chunks_used
            st.session_state["original_text"] = cleaned
            st.session_state["upload_source"] = upload_source
            st.session_state["output_mode"]   = output_mode
            st.session_state["length_choice"] = length_choice
            st.session_state["style_choice"]  = style_choice
            st.session_state["engine_used"]   = engine_label
            st.rerun()

        except RuntimeError as e:
            status_box.update(label="❌ Error during generation", state="error", expanded=True)
            st.error(str(e))
            st.stop()
        except EnvironmentError as e:
            status_box.update(label="⚠️ Configuration required", state="error", expanded=True)
            st.error(f"{e}")
            st.stop()


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------
if "summary" in st.session_state and st.session_state["summary"]:
    summary     = st.session_state["summary"]
    original    = st.session_state.get("original_text", "")
    chunks_used = st.session_state.get("chunks_used", 1)
    src_file    = st.session_state.get("upload_source")
    engine_used = st.session_state.get("engine_used", "")
    om          = st.session_state.get("output_mode",   output_mode)
    lc          = st.session_state.get("length_choice", length_choice)
    sc          = st.session_state.get("style_choice",  style_choice)

    st.markdown('<div class="cyber-divider"></div>', unsafe_allow_html=True)

    badge_html = f'<span class="engine-badge">{engine_used}</span>' if engine_used else ""
    st.markdown(
        f'<div style="font-family:\'Audiowide\',monospace;font-size:1.3rem;'
        f'color:#0e7490;letter-spacing:0.04em;margin-bottom:0.6rem;">'
        f'SUMMARY OUTPUT {badge_html}</div>',
        unsafe_allow_html=True,
    )

    if src_file:
        st.markdown(
            f'<div class="file-badge">📁 Source: <strong>{src_file}</strong></div>',
            unsafe_allow_html=True,
        )

    stats = utils.format_stats(original, summary)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Original Words", f"{stats['original_words']:,}")
    c2.metric("Summary Words",  f"{stats['summary_words']:,}")
    c3.metric("Compression",    stats["ratio_pct"])
    c4.metric("Reduction",      stats["reduction_pct"])

    if chunks_used > 1:
        st.info(f"⚡ Text processed in **{chunks_used} sections** and synthesized into one final summary.")

    st.markdown("")
    st.markdown(f'<div class="summary-box">{summary}</div>', unsafe_allow_html=True)
    st.markdown("")

    st.markdown('<div class="section-header">[ EXPORT OPTIONS ]</div>', unsafe_allow_html=True)

    export_col1, export_col2, export_col3, export_col4, export_col5 = st.columns(5)

    export_kwargs = dict(
        summary=summary,
        stats=stats,
        output_mode=om,
        length_choice=lc,
        style_choice=sc,
        source=src_file,
    )

    with export_col1:
        st.markdown("<div class='export-label'>PDF DOC</div>", unsafe_allow_html=True)
        try:
            pdf_bytes = exporters.to_pdf(**export_kwargs)
            st.download_button("↓ PDF", data=pdf_bytes, file_name="summary_notes.pdf",
                               mime="application/pdf", use_container_width=True, key="dl_pdf")
        except Exception as e:
            st.error(f"PDF error: {e}")

    with export_col2:
        st.markdown("<div class='export-label'>WORD DOC</div>", unsafe_allow_html=True)
        try:
            docx_bytes = exporters.to_docx(**export_kwargs)
            st.download_button("↓ DOCX", data=docx_bytes, file_name="summary_notes.docx",
                               mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                               use_container_width=True, key="dl_docx")
        except Exception as e:
            st.error(f"DOCX error: {e}")

    with export_col3:
        st.markdown("<div class='export-label'>MARKDOWN</div>", unsafe_allow_html=True)
        md_text = exporters.to_markdown(**export_kwargs)
        st.download_button("↓ .MD", data=md_text.encode("utf-8"), file_name="summary_notes.md",
                           mime="text/markdown", use_container_width=True, key="dl_md")

    with export_col4:
        st.markdown("<div class='export-label'>CLIPBOARD</div>", unsafe_allow_html=True)
        with st.expander("[ COPY ]"):
            st.code(summary, language=None)

    with export_col5:
        st.markdown("<div class='export-label'>&nbsp;</div>", unsafe_allow_html=True)
        if st.button("✕ Clear", use_container_width=True, key="clear_btn"):
            for key in ["summary", "chunks_used", "original_text",
                        "upload_source", "output_mode", "length_choice", "style_choice", "engine_used"]:
                st.session_state.pop(key, None)
            st.rerun()
