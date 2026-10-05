"""
summarizer.py - Multi-engine Summarization Engine with Real-Time Streaming.

Supports:
1. NVIDIA NIM: Nemotron 3 Ultra 550B (deep, high-parameter reasoning)
2. Groq Cloud: Llama 3.3 70B / Qwen (ultra-fast, sub-second LPU inference)

Features:
- Token streaming generator for typewriter display via st.write_stream
- Dynamic max_tokens based on selected length
- Smart chunking for long documents
- Streamlit Cloud secrets + .env fallback
- Graceful error handling for missing keys or API limits
"""

import os
import time
from typing import Callable, Optional, Generator, Tuple
from dotenv import load_dotenv

load_dotenv()

from openai import OpenAI, RateLimitError, APITimeoutError, APIError

# ---------------------------------------------------------------------------
# Engine configurations
# ---------------------------------------------------------------------------
ENGINES = {
    "nvidia": {
        "name": "NVIDIA Nemotron 3 Ultra (550B)",
        "base_url": "https://integrate.api.nvidia.com/v1",
        "model": "nvidia/nemotron-3-ultra-550b-a55b",
        "env_key": "NVIDIA_API_KEY",
        "doc_url": "https://build.nvidia.com",
    },
    "groq": {
        "name": "Groq Ultra-Fast (Llama 3.1 8B)",
        "base_url": "https://api.groq.com/openai/v1",
        "model": "meta-llama/llama-3.1-8b-instant",
        "env_key": "GROQ_API_KEY",
        "doc_url": "https://console.groq.com",
    },
}

# ---------------------------------------------------------------------------
# Chunking and Retry configs
# ---------------------------------------------------------------------------
CHUNK_SIZE_WORDS = 1500
CHUNK_OVERLAP_WORDS = 80
MAX_RETRIES = 2
RETRY_DELAY_SEC = 2


def get_secret(key: str, default: str = "") -> str:
    """Retrieve secret from environment or Streamlit secrets."""
    val = os.environ.get(key, "").strip()
    if val:
        return val
    try:
        import streamlit as st
        if hasattr(st, "secrets") and key in st.secrets:
            return str(st.secrets[key]).strip()
    except Exception:
        pass
    return default


# ---------------------------------------------------------------------------
# Client factory
# ---------------------------------------------------------------------------

def get_client(engine: str = "groq", custom_key: Optional[str] = None) -> Tuple[OpenAI, str]:
    """
    Create an OpenAI-compatible client for either NVIDIA NIM or Groq.

    Returns:
        (client, model_name)
    """
    engine_cfg = ENGINES.get(engine, ENGINES["groq"])
    api_key = (custom_key or "").strip() or get_secret(engine_cfg["env_key"])

    if not api_key:
        label = engine_cfg["name"]
        env_var = engine_cfg["env_key"]
        doc = engine_cfg["doc_url"]
        raise EnvironmentError(
            f"API key for {label} is missing.\n\n"
            f"Please enter your `{env_var}` in the sidebar, add it to `.env`, or configure Streamlit Secrets.\n"
            f"Get a free key here: {doc}"
        )

    client = OpenAI(
        base_url=engine_cfg["base_url"],
        api_key=api_key,
        timeout=60.0
    )
    return client, engine_cfg["model"]


# ---------------------------------------------------------------------------
# Prompt engineering
# ---------------------------------------------------------------------------

def _build_system_prompt(mode: str, length: str, style: str) -> str:
    """Construct prompt based on mode, length and style."""
    format_instructions = {
        "bullet": (
            "Present the summary as clean bullet points using '- ' syntax. "
            "Group points logically if appropriate. Do not use roman numerals."
        ),
        "paragraph": (
            "Write the summary as fluent, well-structured prose paragraphs. "
            "Use clear topic sentences for each paragraph."
        ),
    }

    length_instructions = {
        "short": (
            "Keep it very concise - 3 to 5 bullet points or 2 to 3 sentences maximum. "
            "Capture only the core takeaway."
        ),
        "medium": (
            "Provide a balanced summary - 5 to 8 bullet points or 4 to 6 sentences. "
            "Cover major points and essential context."
        ),
        "detailed": (
            "Write a thorough summary - 10 to 15 bullets or 7 to 10 sentences. "
            "Include important supporting details and nuances."
        ),
    }

    style_instructions = {
        "student": (
            "Write for a student: organize by key concepts, definitions, "
            "and core takeaways that would help someone studying for an exam."
        ),
        "executive": (
            "Write for a busy executive: lead with the bottom-line conclusion, "
            "highlight key metrics or decisions, and omit low-level details."
        ),
        "eli5": (
            "Explain it like I'm 5: use everyday language, simple analogies, "
            "and absolutely no jargon. Make complex ideas easy to grasp."
        ),
    }

    fmt = format_instructions.get(mode, format_instructions["paragraph"])
    lng = length_instructions.get(length, length_instructions["medium"])
    sty = style_instructions.get(style, style_instructions["student"])

    return (
        "You are an expert summarizer. Your goal is to distill text accurately, "
        "concisely, and faithfully without hallucinating any facts.\n\n"
        f"Format:\n{fmt}\n\n"
        f"Length:\n{lng}\n\n"
        f"Style / Audience:\n{sty}\n\n"
        "Important rules:\n"
        "- Base your summary ONLY on the provided text.\n"
        "- Do NOT add introductory filler like 'Here is a summary:' or 'In summary,'.\n"
        "- Start directly with the summarized content."
    )


def _build_merge_prompt(mode: str, length: str, style: str) -> str:
    """Prompt for merging multi-section summaries."""
    base = _build_system_prompt(mode, length, style)
    return (
        f"{base}\n\n"
        "You are given partial summaries from sections of a longer document. "
        "Synthesize them into one coherent, unified summary without duplication."
    )


def _split_into_chunks(text: str, chunk_size: int = CHUNK_SIZE_WORDS) -> list[str]:
    """Split long input into overlapping chunks."""
    words = text.split()
    total = len(words)
    if total <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < total:
        end = min(start + chunk_size, total)
        chunks.append(" ".join(words[start:end]))
        if end == total:
            break
        start = end - CHUNK_OVERLAP_WORDS
    return chunks


def _get_max_tokens(length: str, is_chunk: bool = False) -> int:
    """Calculate token ceiling."""
    if is_chunk:
        return 350
    if length == "short":
        return 400
    elif length == "medium":
        return 750
    else:
        return 1400


# ---------------------------------------------------------------------------
# API call with retry
# ---------------------------------------------------------------------------

def _call_api_sync(client: OpenAI, model: str, system_prompt: str, user_content: str, max_tokens: int) -> str:
    """Synchronous single call for intermediate chunks."""
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            res = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.2,
                max_tokens=max_tokens,
            )
            return res.choices[0].message.content.strip()
        except RateLimitError as e:
            last_error = e
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SEC * attempt)
        except APITimeoutError as e:
            last_error = e
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SEC)
        except APIError as e:
            status = getattr(e, "status_code", None)
            if status and 400 <= status < 500 and status != 429:
                raise RuntimeError(f"API Error ({status}): {e.message or str(e)}") from e
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SEC)
        except Exception as e:
            raise RuntimeError(f"Unexpected API error: {e}") from e

    raise RuntimeError("API request failed after retries.") from last_error


# ---------------------------------------------------------------------------
# Streaming API Generator
# ---------------------------------------------------------------------------

def stream_summarize(
    text: str,
    mode: str = "paragraph",
    length: str = "medium",
    style: str = "student",
    engine: str = "groq",
    custom_key: Optional[str] = None,
    status_callback: Optional[Callable[[str], None]] = None,
) -> Tuple[Generator[str, None, None], int]:
    """
    Summarizes text and yields tokens as they arrive for live streaming.

    Returns:
        (token_generator, chunks_count)
    """
    client, model = get_client(engine, custom_key)
    system_prompt = _build_system_prompt(mode, length, style)
    chunks = _split_into_chunks(text)
    total_chunks = len(chunks)
    target_tokens = _get_max_tokens(length, is_chunk=False)

    if total_chunks == 1:
        if status_callback:
            status_callback(f"Streaming from {ENGINES[engine]['name']}...")

        def token_stream() -> Generator[str, None, None]:
            stream = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": chunks[0]},
                ],
                temperature=0.2,
                max_tokens=target_tokens,
                stream=True
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                if delta:
                    yield delta

        return token_stream(), 1

    # Multiple chunks: summarize chunks sequentially, then stream the final merge
    chunk_tokens = _get_max_tokens(length, is_chunk=True)
    partial_summaries = []

    for i, chunk in enumerate(chunks, start=1):
        if status_callback:
            status_callback(f"Analyzing section {i} of {total_chunks}...")
        user_msg = f"[Section {i} of {total_chunks}]\n\n{chunk}"
        part = _call_api_sync(client, model, system_prompt, user_msg, max_tokens=chunk_tokens)
        partial_summaries.append(f"[Section {i}]\n{part}")

    if status_callback:
        status_callback("Synthesizing final summary...")

    merge_prompt = _build_merge_prompt(mode, length, style)
    combined = "\n\n".join(partial_summaries)

    def merge_stream() -> Generator[str, None, None]:
        stream = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": merge_prompt},
                {"role": "user", "content": combined},
            ],
            temperature=0.2,
            max_tokens=target_tokens,
            stream=True
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            if delta:
                yield delta

    return merge_stream(), total_chunks


def summarize(
    text: str,
    mode: str = "paragraph",
    length: str = "medium",
    style: str = "student",
    engine: str = "groq",
    custom_key: Optional[str] = None,
    progress_callback: Optional[Callable[[str, int, int], None]] = None,
) -> Tuple[str, int]:
    """Synchronous complete call that gathers the stream into a single string."""
    status_fn = (lambda msg: progress_callback(msg, 1, 1)) if progress_callback else None
    stream, chunks = stream_summarize(
        text=text,
        mode=mode,
        length=length,
        style=style,
        engine=engine,
        custom_key=custom_key,
        status_callback=status_fn
    )
    full_text = "".join(list(stream))
    return full_text, chunks
