"""
exporters.py — Functions to export the AI-generated summary as a
               formatted PDF, DOCX, or Markdown (.md) file.

Each public function takes the same arguments:
    summary       : str  — The final summary text from the API.
    stats         : dict — Word-count stats dict from utils.format_stats().
    output_mode   : str  — "Bullet Points" or "Short Paragraph" (display label).
    length_choice : str  — "Short", "Medium", or "Detailed".
    style_choice  : str  — "Student Notes", "Executive Brief", or "Simple (ELI5)".
    source        : str  — Filename if input came from an upload, else None.

Return values:
    to_markdown() -> str       (plain text — caller saves as .md)
    to_docx()     -> BytesIO   (binary Word document bytes)
    to_pdf()      -> BytesIO   (binary PDF document bytes)
"""

import io
import re
from datetime import datetime


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _parse_bullet_lines(text: str) -> list:
    """
    Split *text* into a list of (is_bullet, line_text) tuples.

    A line is treated as a bullet if it starts with:
        -  a dash      (-)
        -  an asterisk (*)
        -  a bullet    (U+2022 •)
    followed by at least one space.

    Returns
    -------
    list of (bool, str)
        bool  — True  if the line is a bullet point.
        str   — The line content WITHOUT the leading bullet symbol.
    """
    results = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue  # blank lines: exporters add their own spacing
        if re.match(r'^[-*\u2022]\s+', stripped):
            # Strip the bullet marker and keep only content
            content = re.sub(r'^[-*\u2022]\s+', '', stripped)
            results.append((True, content))
        else:
            results.append((False, stripped))
    return results


def _meta_lines(output_mode, length_choice, style_choice, stats, source):
    """
    Return an ordered list of 'Key : Value' strings shown at the top of
    every exported file so the reader always has context.
    """
    lines = []
    if source:
        lines.append(f"Source       : {source}")
    lines += [
        f"Mode         : {output_mode}",
        f"Length       : {length_choice}",
        f"Style        : {style_choice}",
        f"Original     : {stats['original_words']:,} words",
        f"Summary      : {stats['summary_words']:,} words",
        f"Compression  : {stats['ratio_pct']} ({stats['reduction_pct']})",
        f"Generated    : {datetime.now().strftime('%Y-%m-%d %H:%M')}",
    ]
    return lines


# ---------------------------------------------------------------------------
# Markdown export
# ---------------------------------------------------------------------------

def to_markdown(
    summary: str,
    stats: dict,
    output_mode: str,
    length_choice: str,
    style_choice: str,
    source: str = None,
) -> str:
    """
    Return the summary as a Markdown string.

    Structure
    ---------
    # AI Summary Notes
    > metadata (blockquote)
    ---
    The summary text (the model already outputs valid Markdown, so no
    transformation is needed — bullet lists and paragraphs work as-is).
    """
    lines = ["# AI Summary Notes", ""]

    # Metadata as a GitHub-style blockquote
    for meta in _meta_lines(output_mode, length_choice, style_choice, stats, source):
        lines.append(f"> {meta}")

    lines += ["", "---", "", summary, ""]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# DOCX export
# ---------------------------------------------------------------------------

def to_docx(
    summary: str,
    stats: dict,
    output_mode: str,
    length_choice: str,
    style_choice: str,
    source: str = None,
) -> io.BytesIO:
    """
    Return a BytesIO object with a formatted .docx Word document inside.

    Structure
    ---------
    Heading  : "AI Summary Notes"  (large, purple, centred)
    Metadata : key-value table
    Divider
    Body     : bullet list paragraphs OR plain paragraphs
    """
    from docx import Document
    from docx.shared import Pt, RGBColor, Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement

    doc = Document()

    # ---- Page margins ----
    for section in doc.sections:
        section.top_margin    = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin   = Inches(1.2)
        section.right_margin  = Inches(1.2)

    # ---- Title ----
    title_para = doc.add_paragraph()
    title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title_para.add_run("AI Summary Notes")
    run.bold           = True
    run.font.size      = Pt(22)
    run.font.color.rgb = RGBColor(0x5B, 0x21, 0xB6)   # deep purple
    doc.add_paragraph()  # blank line

    # ---- Metadata block ----
    for meta in _meta_lines(output_mode, length_choice, style_choice, stats, source):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        if " : " in meta:
            key, val = meta.split(" : ", 1)
            key_run = p.add_run(key + " : ")
            key_run.bold           = True
            key_run.font.color.rgb = RGBColor(0x6D, 0x28, 0xD9)
            p.add_run(val)
        else:
            p.add_run(meta)

    # ---- Divider — a paragraph with a bottom border ----
    doc.add_paragraph()
    divider_para = doc.add_paragraph()
    pPr  = divider_para._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bot  = OxmlElement("w:bottom")
    bot.set(qn("w:val"),   "single")
    bot.set(qn("w:sz"),    "6")
    bot.set(qn("w:space"), "1")
    bot.set(qn("w:color"), "7C3AED")
    pBdr.append(bot)
    pPr.append(pBdr)
    doc.add_paragraph()  # breathing room

    # ---- Summary body ----
    parsed = _parse_bullet_lines(summary)
    if parsed:
        for is_bullet, content in parsed:
            if is_bullet:
                # Word's built-in "List Bullet" style handles indentation
                p = doc.add_paragraph(style="List Bullet")
                run = p.add_run(content)
                run.font.size = Pt(11)
            else:
                p = doc.add_paragraph()
                run = p.add_run(content)
                run.font.size = Pt(11)
                p.paragraph_format.space_after = Pt(6)
    else:
        doc.add_paragraph(summary)

    # ---- Return as BytesIO ----
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf


# ---------------------------------------------------------------------------
# PDF export
# ---------------------------------------------------------------------------

def to_pdf(
    summary: str,
    stats: dict,
    output_mode: str,
    length_choice: str,
    style_choice: str,
    source: str = None,
) -> io.BytesIO:
    """
    Return a BytesIO object with a styled .pdf file inside.

    Uses fpdf2 — a lightweight, zero-dependency PDF library.

    Structure
    ---------
    Purple header bar  : title + subtitle
    Metadata box       : light-purple background, bold keys
    Divider line
    Body               : bullet lines (purple dot + indented text)
                         OR plain paragraphs
    Footer             : page number on every page
    """
    from fpdf import FPDF

    # ---- Sub-class FPDF so every page gets a footer automatically ----
    class SummaryPDF(FPDF):
        def header(self):
            pass  # drawn manually on page 1 only

        def footer(self):
            self.set_y(-15)
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(150, 150, 150)
            self.cell(0, 10, f"AI Text Summarizer  |  Page {self.page_no()}", align="C")

    pdf = SummaryPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_margins(20, 20, 20)

    # ---- Purple header bar (full-width rectangle) ----
    pdf.set_fill_color(92, 33, 182)         # deep purple  #5B21B6
    pdf.rect(0, 0, 210, 30, style="F")

    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(0, 7)
    pdf.cell(210, 10, "AI Summary Notes", align="C")

    pdf.set_font("Helvetica", "", 9)
    pdf.set_xy(0, 19)
    pdf.cell(210, 8, "Generated by AI Text Summarizer  |  NVIDIA Nemotron Ultra", align="C")

    pdf.ln(16)   # vertical gap below header

    # ---- Metadata box ----
    meta = _meta_lines(output_mode, length_choice, style_choice, stats, source)
    line_h = 7
    box_x  = 20
    box_y  = pdf.get_y()
    box_w  = 170
    box_h  = len(meta) * line_h + 8

    pdf.set_fill_color(245, 243, 255)       # very light lavender
    pdf.rect(box_x, box_y, box_w, box_h, style="F")

    pdf.set_xy(box_x + 4, box_y + 4)
    for item in meta:
        if " : " in item:
            key, val = item.split(" : ", 1)
            # Bold purple key
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(92, 33, 182)
            pdf.set_x(box_x + 4)
            pdf.cell(38, line_h, key + " :", ln=0)
            # Regular dark value
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(30, 30, 30)
            pdf.cell(0, line_h, val, ln=1)
        else:
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(30, 30, 30)
            pdf.cell(0, line_h, item, ln=1)

    pdf.ln(5)

    # ---- Divider line ----
    pdf.set_draw_color(92, 33, 182)
    pdf.set_line_width(0.5)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(7)

    # ---- Summary body ----
    pdf.set_text_color(20, 20, 20)
    parsed = _parse_bullet_lines(summary)

    if parsed:
        for is_bullet, content in parsed:
            if is_bullet:
                # Purple bullet dot
                pdf.set_font("Helvetica", "B", 12)
                pdf.set_text_color(92, 33, 182)
                pdf.set_x(20)
                pdf.cell(7, 7, "\u2022", ln=0)
                # Content text, indented, wraps automatically
                pdf.set_font("Helvetica", "", 11)
                pdf.set_text_color(20, 20, 20)
                pdf.set_x(27)
                pdf.multi_cell(163, 7, content)
                pdf.ln(1)
            else:
                pdf.set_font("Helvetica", "", 11)
                pdf.set_text_color(20, 20, 20)
                pdf.set_x(20)
                pdf.multi_cell(170, 7, content)
                pdf.ln(3)
    else:
        # Plain fallback
        pdf.set_font("Helvetica", "", 11)
        pdf.set_x(20)
        pdf.multi_cell(170, 7, summary)

    # ---- Return as BytesIO ----
    buf = io.BytesIO(pdf.output())
    buf.seek(0)
    return buf
