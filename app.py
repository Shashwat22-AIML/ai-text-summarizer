"""
app.py - Streamlit UI for the AI Text Summarizer with Multi-Engine & Live Streaming.

Run with:
    python -m streamlit run app.py

Features:
    - AI Engine Selector: Groq Ultra-Fast (Sub-second) vs NVIDIA Nemotron 3 Ultra
    - Real-time Token Streaming via st.write_stream
    - Document Upload (.pdf, .docx, .txt) + Manual Paste
    - Multi-format Export: PDF, DOCX, Markdown, Copy to Clipboard
    - Premium White + Cyan ClubFlux-inspired theme
    - Full Streamlit Cloud & local .env support
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
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS - White + Cyan Theme
# ---------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Audiowide&family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* --- GLOBAL BASE --- */
html, body, .stApp {
    background-color: #f8fafc !important;
    color: #0f172a !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}

/* Background subtle cyan grid */
.stApp::before {
    content: '';
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background-image: 
        radial-gradient(circle at 15% 15%, rgba(6, 182, 212, 0.08) 0%, transparent 40%),
        radial-gradient(circle at 85% 85%, rgba(14, 165, 233, 0.06) 0%, transparent 40%);
    pointer-events: none;
    z-index: 0;
}

/* --- SIDEBAR --- */
section[data-testid="stSidebar"] {
    background-color: #ffffff !important;
    border-right: 1.5px solid #e2e8f0 !important;
    box-shadow: 4px 0 24px rgba(6, 182, 212, 0.04) !important;
}
section[data-testid="stSidebar"] * {
    color: #1e293b !important;
}
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    font-family: 'Audiowide', sans-serif !important;
    color: #0891b2 !important;
    font-size: 0.82rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
}

/* --- TITLES & BADGES --- */
.cyber-title {
    font-family: 'Audiowide', sans-serif;
    font-size: 2.2rem;
    font-weight: 800;
    color: #0f172a;
    letter-spacing: 0.05em;
    margin-bottom: 0.2rem;
    background: linear-gradient(135deg, #0f172a 30%, #0891b2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.cyber-subtitle {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
    color: #64748b;
    letter-spacing: 0.04em;
    margin-bottom: 1.2rem;
}

.cyber-badge {
    display: inline-block;
    padding: 0.25rem 0.65rem;
    margin-right: 0.4rem;
    margin-bottom: 0.5rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    font-weight: 600;
    border-radius: 9999px;
    background: #ecfeff;
    color: #0891b2;
    border: 1px solid #a5f3fc;
}

.cyber-divider {
    height: 2px;
    background: linear-gradient(90deg, #06b6d4 0%, #38bdf8 50%, transparent 100%);
    margin: 1rem 0 1.5rem 0;
    border-radius: 2px;
}

/* --- BUTTONS --- */
.stButton > button {
    background: linear-gradient(135deg, #06b6d4 0%, #0284c7 100%) !important;
    color: #ffffff !important;
    font-family: 'Audiowide', sans-serif !important;
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.06em !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.65rem 1.4rem !important;
    box-shadow: 0 4px 14px rgba(6, 182, 212, 0.35) !important;
    transition: all 0.2s ease-in-out !important;
    width: 100% !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(6, 182, 212, 0.45) !important;
    background: linear-gradient(135deg, #0891b2 0%, #0369a1 100%) !important;
}

/* Download buttons */
.stDownloadButton > button {
    background: #ffffff !important;
    color: #0891b2 !important;
    border: 1.5px solid #06b6d4 !important;
    border-radius: 8px !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    padding: 0.45rem 1rem !important;
    box-shadow: 0 2px 8px rgba(6, 182, 212, 0.08) !important;
    transition: all 0.15s ease !important;
    width: 100% !important;
}
.stDownloadButton > button:hover {
    background: #ecfeff !important;
    border-color: #0891b2 !important;
    transform: translateY(-1px) !important;
}

/* --- CARDS & BOXES --- */
.metric-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-top: 3px solid #06b6d4;
    border-radius: 10px;
    padding: 0.85rem 1.1rem;
    box-shadow: 0 2px 10px rgba(15, 23, 42, 0.03);
    text-align: center;
}
.metric-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.45rem;
    font-weight: 700;
    color: #0891b2;
}
.metric-label {
    font-size: 0.75rem;
    font-weight: 600;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-top: 0.2rem;
}

.output-container {
    background: #ffffff;
    border: 1.5px solid #cbd5e1;
    border-left: 4px solid #06b6d4;
    border-radius: 10px;
    padding: 1.4rem;
    margin-top: 1rem;
    box-shadow: 0 4px 16px rgba(15, 23, 42, 0.04);
}
.output-tag {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    font-weight: 700;
    color: #0891b2;
    background: #ecfeff;
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    border: 1px solid #a5f3fc;
    display: inline-block;
    margin-bottom: 0.8rem;
}

/* Input textareas */
.stTextArea textarea {
    background-color: #ffffff !important;
    color: #0f172a !important;
    border: 1.5px solid #cbd5e1 !important;
    border-radius: 10px !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 0.95rem !important;
}
.stTextArea textarea:focus {
    border-color: #06b6d4 !important;
    box-shadow: 0 0 0 3px rgba(6, 182, 212, 0.15) !important;
}

/* Custom scrollbars */
::-webkit-scrollbar {
    width: 7px;
    height: 7px;
}
::-webkit-scrollbar-track {
    background: #f1f5f9;
}
::-webkit-scrollbar-thumb {
    background: #94a3b8;
    border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
    background: #0891b2;
}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Helper: Secret Resolver
# ---------------------------------------------------------------------------
def get_secret(key: str, default: str = "") -> str:
    val = os.environ.get(key, "").strip()
    if val:
        return val
    try:
        if hasattr(st, "secrets") and key in st.secrets:
            return str(st.secrets[key]).strip()
    except Exception:
        pass
    return default


# ---------------------------------------------------------------------------
# Sidebar - Configuration
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚡ AI CONFIGURATION")
    st.markdown("---")

    has_groq_key = bool(get_secret("GROQ_API_KEY"))
    has_nvidia_key = bool(get_secret("NVIDIA_API_KEY"))

    st.markdown("**Select AI Engine**")
    engine_choice = st.radio(
        label="AI Engine",
        options=["⚡ Groq Ultra-Fast (Sub-second)", "🧠 NVIDIA Nemotron 3 Ultra (550B)"],
        index=0 if has_groq_key or not has_nvidia_key else 1,
        help="Groq delivers instant sub-second summaries. NVIDIA Nemotron uses a massive 550B model.",
        label_visibility="collapsed",
    )
    engine_key = "groq" if "Groq" in engine_choice else "nvidia"

    custom_key = None
    if engine_key == "groq" and not has_groq_key:
        st.info("💡 **Groq is 100% Free & 10x faster!** Get your key at [console.groq.com](https://console.groq.com)")
        custom_key = st.text_input(
            "Groq API Key", type="password", placeholder="gsk_...",
            help="Paste your Groq API key here"
        )
    elif engine_key == "nvidia" and not has_nvidia_key:
        st.info("💡 Get your NVIDIA key at [build.nvidia.com](https://build.nvidia.com)")
        custom_key = st.text_input(
            "NVIDIA API Key", type="password", placeholder="nvapi-...",
            help="Paste your NVIDIA API key here"
        )

    st.markdown("---")
    st.markdown("**Output Format**")
    output_mode = st.radio(
        label="Output Mode",
        options=["Bullet Points", "Short Paragraph"],
        index=0,
        label_visibility="collapsed",
    )
    mode_key = "bullet" if output_mode == "Bullet Points" else "paragraph"

    st.markdown("---")
    st.markdown("**Summary Length**")
    length_choice = st.radio(
        label="Summary Length",
        options=["Short", "Medium", "Detailed"],
        index=1,
        label_visibility="collapsed",
    )
    length_key = length_choice.lower()

    st.markdown("---")
    st.markdown("**Audience Style**")
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
        """<div style="font-family:'JetBrains Mono',monospace;font-size:0.7rem;color:#94a3b8;text-align:center;letter-spacing:0.04em;padding:0.4rem 0;">
        AI TEXT SUMMARIZER v2.0<br>POWERED BY GROQ &amp; NVIDIA
        </div>""",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Main - Hero Header
# ---------------------------------------------------------------------------
st.markdown('<div class="cyber-title">AI TEXT SUMMARIZER</div>', unsafe_allow_html=True)
st.markdown('<div class="cyber-subtitle">// Neural Compression Engine &nbsp;•&nbsp; Multi-Model &nbsp;•&nbsp; Live Streaming</div>', unsafe_allow_html=True)
st.markdown('<div class="cyber-divider"></div>', unsafe_allow_html=True)

st.markdown(
    '<span class="cyber-badge">⚡ GROQ LPU</span>'
    '<span class="cyber-badge">🧠 NVIDIA NIM</span>'
    '<span class="cyber-badge">📡 REAL-TIME STREAM</span>'
    '<span class="cyber-badge">📄 MULTI-EXPORT</span>',
    unsafe_allow_html=True,
)
st.markdown("")


# ---------------------------------------------------------------------------
# State Management
# ---------------------------------------------------------------------------
if "summary_result" not in st.session_state:
    st.session_state.summary_result = ""
if "summary_stats" not in st.session_state:
    st.session_state.summary_stats = {}
if "original_input" not in st.session_state:
    st.session_state.original_input = ""
if "source_name" not in st.session_state:
    st.session_state.source_name = "Direct Paste"


# ---------------------------------------------------------------------------
# Input Section - Tabs
# ---------------------------------------------------------------------------
tab_paste, tab_upload = st.tabs(["📝 Paste Text", "📁 Upload Document"])

raw_text = ""
source_label = "Direct Paste"

with tab_paste:
    pasted_text = st.text_area(
        label="Input Text",
        height=220,
        placeholder="Paste your article, meeting notes, research paper, or essay here (minimum 30 words)...",
        label_visibility="collapsed",
    )
    if pasted_text:
        raw_text = pasted_text
        source_label = "Direct Paste"

with tab_upload:
    uploaded_file = st.file_uploader(
        "Choose a file (.txt, .pdf, .docx)",
        type=["txt", "pdf", "docx"],
        help="Upload text files, PDF documents, or Word files to extract and summarize.",
    )
    if uploaded_file is not None:
        extracted_text, err = utils.extract_text_from_file(uploaded_file)
        if err:
            st.error(f"⚠️ {err}")
        else:
            raw_text = extracted_text
            source_label = uploaded_file.name
            st.success(f"✅ Loaded **{uploaded_file.name}** ({utils.count_words(raw_text):,} words)")


# ---------------------------------------------------------------------------
# Action Buttons & Execution
# ---------------------------------------------------------------------------
col_btn1, col_btn2 = st.columns([3, 1])

with col_btn1:
    summarize_clicked = st.button("⚡ GENERATE SUMMARY", use_container_width=True)

with col_btn2:
    if st.button("🗑️ Clear", use_container_width=True):
        st.session_state.summary_result = ""
        st.session_state.summary_stats = {}
        st.session_state.original_input = ""
        st.session_state.source_name = "Direct Paste"
        st.rerun()

if summarize_clicked:
    cleaned = utils.clean_text(raw_text)
    is_valid, validation_msg = utils.validate_input(cleaned)

    if not is_valid:
        st.warning(validation_msg)
    else:
        st.session_state.original_input = cleaned
        st.session_state.source_name = source_label

        try:
            status_placeholder = st.empty()
            summary_placeholder = st.empty()

            def update_status(msg: str):
                status_placeholder.info(f"⏳ {msg}")

            token_stream, chunks_count = summarizer.stream_summarize(
                text=cleaned,
                mode=mode_key,
                length=length_key,
                style=style_key,
                engine=engine_key,
                custom_key=custom_key,
                status_callback=update_status,
            )

            with summary_placeholder.container():
                st.markdown('<div class="output-container"><div class="output-tag">[ LIVE STREAMING ]</div>', unsafe_allow_html=True)
                full_summary = st.write_stream(token_stream)
                st.markdown('</div>', unsafe_allow_html=True)

            status_placeholder.empty()

            # Save results
            st.session_state.summary_result = full_summary
            st.session_state.summary_stats = utils.format_stats(cleaned, full_summary)
            st.rerun()

        except EnvironmentError as e:
            st.error(f"🔑 **Missing API Key**:\n\n{e}")
        except Exception as e:
            st.error(f"⚠️ **Summarization Error**: {e}")


# ---------------------------------------------------------------------------
# Output Display & Metrics
# ---------------------------------------------------------------------------
if st.session_state.summary_result:
    stats = st.session_state.summary_stats
    orig_words = stats.get("original_words", 0)
    summ_words = stats.get("summary_words", 0)
    reduc_pct = stats.get("reduction_pct", "0%")

    st.markdown("### 📊 Summary Metrics")
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{orig_words:,}</div><div class="metric-label">Original Words</div></div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{summ_words:,}</div><div class="metric-label">Summary Words</div></div>', unsafe_allow_html=True)
    with m3:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{reduc_pct}</div><div class="metric-label">Reduction</div></div>', unsafe_allow_html=True)
    with m4:
        reading_time = max(1, round(summ_words / 200))
        st.markdown(f'<div class="metric-card"><div class="metric-value">~{reading_time} min</div><div class="metric-label">Reading Time</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="output-container">', unsafe_allow_html=True)
    st.markdown(f'<div class="output-tag">[ SUMMARY OUTPUT • {output_mode.upper()} ]</div>', unsafe_allow_html=True)
    st.markdown(st.session_state.summary_result)
    st.markdown('</div>', unsafe_allow_html=True)

    # Export options
    st.markdown("### 📥 Export & Download")
    e1, e2, e3 = st.columns(3)

    with e1:
        md_data = exporters.to_markdown(
            summary=st.session_state.summary_result,
            stats=stats,
            output_mode=output_mode,
            length_choice=length_choice,
            style_choice=style_choice,
            source=st.session_state.source_name,
        )
        st.download_button(
            label="📄 Download Markdown (.md)",
            data=md_data,
            file_name="ai_summary.md",
            mime="text/markdown",
            use_container_width=True,
        )

    with e2:
        try:
            pdf_buf = exporters.to_pdf(
                summary=st.session_state.summary_result,
                stats=stats,
                output_mode=output_mode,
                length_choice=length_choice,
                style_choice=style_choice,
                source=st.session_state.source_name,
            )
            st.download_button(
                label="📕 Download PDF (.pdf)",
                data=pdf_buf,
                file_name="ai_summary.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as ex:
            st.warning(f"PDF export unavailable: {ex}")

    with e3:
        try:
            docx_buf = exporters.to_docx(
                summary=st.session_state.summary_result,
                stats=stats,
                output_mode=output_mode,
                length_choice=length_choice,
                style_choice=style_choice,
                source=st.session_state.source_name,
            )
            st.download_button(
                label="📘 Download Word (.docx)",
                data=docx_buf,
                file_name="ai_summary.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
            )
        except Exception as ex:
            st.warning(f"DOCX export unavailable: {ex}")
