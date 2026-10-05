"""
utils.py - Helper utilities for text cleaning, word-count statistics,
           and document text extraction.

These functions are kept separate from the API logic so they can be tested
and reused without importing anything related to NVIDIA / OpenAI.
"""

import re
import io

# ---------------------------------------------------------------------------
# Text cleaning
# ---------------------------------------------------------------------------

def clean_text(text: str) -> str:
    """
    Normalize whitespace in *text* and strip leading/trailing spaces.

    Steps
    -----
    1. Replace tabs and carriage-returns with plain spaces.
    2. Collapse runs of blank lines (paragraph breaks) into a single blank line.
    3. Collapse multiple spaces into one within each line.
    4. Strip the whole string.

    Returns
    -------
    str
        Cleaned version of the input text.
    """
    if not text:
        return ""

    # Replace tabs and carriage-returns with a plain space first.
    text = text.replace("\t", " ").replace("\r", "")

    # Collapse multiple blank lines into one (preserves paragraph structure).
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Collapse multiple spaces into one within each line.
    lines = [re.sub(r" {2,}", " ", line) for line in text.split("\n")]
    text = "\n".join(lines)

    return text.strip()


# ---------------------------------------------------------------------------
# Document text extraction
# ---------------------------------------------------------------------------

def extract_text_from_file(uploaded_file) -> tuple[str, str]:
    """
    Extract plain text from an uploaded file object (from st.file_uploader).

    Supported formats
    -----------------
    .txt  - decoded as UTF-8 (falls back to latin-1 if needed)
    .pdf  - extracted with pdfplumber (handles most modern PDFs)
    .docx - extracted with python-docx (paragraph text only)

    Parameters
    ----------
    uploaded_file : UploadedFile
        The file object returned by st.file_uploader().

    Returns
    -------
    (text, error_message)
        text          : str - Extracted text (empty string on failure).
        error_message : str - Human-readable error (empty string on success).
    """
    filename = uploaded_file.name.lower()
    if hasattr(uploaded_file, "seek"):
        uploaded_file.seek(0)
    file_bytes = uploaded_file.read()  # read raw bytes once

    # ---- Plain text (.txt) ----
    if filename.endswith(".txt"):
        try:
            return file_bytes.decode("utf-8"), ""
        except UnicodeDecodeError:
            # Fall back to latin-1 which never raises on any byte sequence
            return file_bytes.decode("latin-1"), ""

    # ---- PDF (.pdf) ----
    elif filename.endswith(".pdf"):
        try:
            import pdfplumber  # imported here so missing package gives a clear error
            pages_text = []
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:  # some pages may be image-only (scanned)
                        pages_text.append(page_text)

            if not pages_text:
                return "", (
                    "Could not extract any text from this PDF. "
                    "It may be a scanned/image-based PDF. "
                    "Try copying the text manually and pasting it instead."
                )
            return "\n\n".join(pages_text), ""

        except ImportError:
            return "", "pdfplumber is not installed. Run: pip install pdfplumber"
        except Exception as e:
            return "", f"Failed to read PDF: {e}"

    # ---- Word document (.docx) ----
    elif filename.endswith(".docx"):
        try:
            from docx import Document  # python-docx
            doc = Document(io.BytesIO(file_bytes))
            # Each paragraph in .docx is a separate object; join with newlines.
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            if not paragraphs:
                return "", "The Word document appears to be empty."
            return "\n\n".join(paragraphs), ""

        except ImportError:
            return "", "python-docx is not installed. Run: pip install python-docx"
        except Exception as e:
            return "", f"Failed to read DOCX: {e}"

    # ---- Unsupported format ----
    else:
        ext = uploaded_file.name.rsplit(".", 1)[-1].upper() if "." in uploaded_file.name else "unknown"
        return "", (
            f"Unsupported file type: .{ext}. "
            "Please upload a .txt, .pdf, or .docx file."
        )


# ---------------------------------------------------------------------------
# Word-count helpers
# ---------------------------------------------------------------------------

def count_words(text: str) -> int:
    """
    Return the number of words in *text*.

    A "word" is any non-whitespace token - matching the behaviour most users
    expect when they paste prose into a text field.

    Parameters
    ----------
    text : str
        Any string (may be empty).

    Returns
    -------
    int
        Word count, 0 for an empty or whitespace-only string.
    """
    if not text or not text.strip():
        return 0
    return len(text.split())


def compression_ratio(original_word_count: int, summary_word_count: int) -> float:
    """
    Calculate how much shorter the summary is relative to the original.

    Formula: summary_words / original_words  (lower = more compressed).

    Returns 0.0 if *original_word_count* is zero to avoid division-by-zero.
    """
    if original_word_count == 0:
        return 0.0
    return summary_word_count / original_word_count


def format_stats(original_text: str, summary_text: str) -> dict:
    """
    Build a statistics dictionary ready for display in the Streamlit UI.

    Returns
    -------
    dict with keys:
        original_words  : int
        summary_words   : int
        ratio           : float  (compression ratio, 0-1)
        ratio_pct       : str    e.g. "23.0%"
        reduction_pct   : str    e.g. "77.0% shorter"
    """
    orig = count_words(original_text)
    summ = count_words(summary_text)
    ratio = compression_ratio(orig, summ)

    reduction = max(0.0, 1.0 - ratio)  # clamp to 0 so we never show negative

    return {
        "original_words": orig,
        "summary_words": summ,
        "ratio": ratio,
        "ratio_pct": f"{ratio * 100:.1f}%",
        "reduction_pct": f"{reduction * 100:.1f}% shorter",
    }


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

MIN_WORDS = 30  # texts shorter than this are rejected before calling the API


def validate_input(text: str) -> tuple[bool, str]:
    """
    Check whether *text* is suitable for summarization.

    Returns
    -------
    (True, "")                  if the text passes validation.
    (False, reason_message)     if it does not.
    """
    if not text or not text.strip():
        return False, "Please paste some text or upload a file before clicking Summarize."

    wc = count_words(text)
    if wc < MIN_WORDS:
        return (
            False,
            f"Your text has only **{wc} word{'s' if wc != 1 else ''}**. "
            f"Please provide at least **{MIN_WORDS} words** so there is enough "
            "content to summarize meaningfully.",
        )

    return True, ""

# Alias for compatibility
word_count = count_words
