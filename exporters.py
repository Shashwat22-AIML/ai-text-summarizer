"""
exporters.py - Export utilities for AI Text Summarizer.

Supports:
1. Markdown (.md) - Plain formatted markdown with metadata header
2. Word Document (.docx) - Formatted with headings, metadata table, styled bullets
3. PDF Document (.pdf) - Cyan header banner, metadata card, styled bullet list via fpdf2
"""

import io
from datetime import datetime


def _meta_lines(output_mode: str, length_choice: str, style_choice: str, stats: dict, source: str = None) -> list[str]:
    """Build standardized metadata lines for document headers."""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        f"Date Generated : {now_str}",
        f"Format / Style : {output_mode.title()} | {length_choice.title()} Length | {style_choice.title()} Audience",
    ]
    if source:
        lines.append(f"Source Document : {source}")
    if stats:
        orig = stats.get("original_words", 0)
        summ = stats.get("summary_words", 0)
        reduc = stats.get("reduction_pct", "")
        lines.append(f"Word Counts     : {orig} original -> {summ} summary ({reduc})")
    return lines


def _parse_bullet_lines(summary: str) -> list[tuple[bool, str]]:
    """Parse markdown summary into (is_bullet, content) tuples."""
    parsed = []
    for line in summary.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(("- ", "* ", "+ ")) or (len(stripped) > 2 and stripped[0].isdigit() and stripped[1] in [".", ")"]):
            # Remove the marker
            if stripped.startswith(("- ", "* ", "+ ")):
                content = stripped[2:].strip()
            else:
                content = stripped.split(" ", 1)[-1].strip() if " " in stripped else stripped
            parsed.append((True, content))
        else:
            parsed.append((False, stripped))
    return parsed


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
    """Return the summary as a clean Markdown string."""
    lines = ["# AI Summary Notes", ""]

    # Metadata as blockquote
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
    """Return a BytesIO object with a styled .docx Word document."""
    from docx import Document
    from docx.shared import Pt, RGBColor, Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement

    doc = Document()

    # Margins
    for section in doc.sections:
        section.top_margin    = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin   = Inches(1.1)
        section.right_margin  = Inches(1.1)

    # Title
    title_para = doc.add_paragraph()
    title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title_para.add_run("AI Summary Notes")
    run.bold = True
    run.font.size = Pt(22)
    run.font.color.rgb = RGBColor(0x08, 0x91, 0xB2)  # Cyan #0891b2
    doc.add_paragraph()

    # Metadata block
    for meta in _meta_lines(output_mode, length_choice, style_choice, stats, source):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        if " : " in meta:
            key, val = meta.split(" : ", 1)
            key_run = p.add_run(key + " : ")
            key_run.bold = True
            key_run.font.color.rgb = RGBColor(0x06, 0xB6, 0xD4)
            p.add_run(val)
        else:
            p.add_run(meta)

    # Divider
    doc.add_paragraph()
    divider_para = doc.add_paragraph()
    pPr  = divider_para._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bot  = OxmlElement("w:bottom")
    bot.set(qn("w:val"),   "single")
    bot.set(qn("w:sz"),    "6")
    bot.set(qn("w:space"), "1")
    bot.set(qn("w:color"), "06B6D4")
    pBdr.append(bot)
    pPr.append(pBdr)
    doc.add_paragraph()

    # Summary body
    parsed = _parse_bullet_lines(summary)
    if parsed:
        for is_bullet, content in parsed:
            if is_bullet:
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
    """Return a BytesIO object with a styled .pdf file."""
    from fpdf import FPDF

    class SummaryPDF(FPDF):
        def header(self):
            pass

        def footer(self):
            self.set_y(-15)
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(140, 150, 160)
            self.cell(0, 10, f"AI Text Summarizer  |  Page {self.page_no()}", align="C")

    pdf = SummaryPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_margins(20, 20, 20)

    # Cyan header bar
    pdf.set_fill_color(8, 145, 178)  # #0891b2
    pdf.rect(0, 0, 210, 30, style="F")

    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(0, 7)
    pdf.cell(210, 10, "AI SUMMARY NOTES", align="C")

    pdf.set_font("Helvetica", "", 9)
    pdf.set_xy(0, 19)
    pdf.cell(210, 8, "Generated by AI Text Summarizer", align="C")

    pdf.ln(16)

    # Metadata card
    meta = _meta_lines(output_mode, length_choice, style_choice, stats, source)
    line_h = 6.5
    box_x  = 20
    box_y  = pdf.get_y()
    box_w  = 170
    box_h  = len(meta) * line_h + 8

    pdf.set_fill_color(240, 250, 251)  # #f0fafb
    pdf.rect(box_x, box_y, box_w, box_h, style="F")

    pdf.set_xy(box_x + 4, box_y + 4)
    for item in meta:
        if " : " in item:
            key, val = item.split(" : ", 1)
            pdf.set_font("Helvetica", "B", 8.5)
            pdf.set_text_color(8, 145, 178)
            pdf.set_x(box_x + 4)
            pdf.cell(38, line_h, key + " :", ln=0)
            pdf.set_font("Helvetica", "", 8.5)
            pdf.set_text_color(30, 41, 59)
            pdf.cell(0, line_h, val, ln=1)
        else:
            pdf.set_font("Helvetica", "", 8.5)
            pdf.set_text_color(30, 41, 59)
            pdf.cell(0, line_h, item, ln=1)

    pdf.ln(5)

    # Divider line
    pdf.set_draw_color(6, 182, 212)
    pdf.set_line_width(0.5)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(7)

    # Summary body
    pdf.set_text_color(30, 41, 59)
    parsed = _parse_bullet_lines(summary)

    if parsed:
        for is_bullet, content in parsed:
            if is_bullet:
                pdf.set_font("Helvetica", "B", 11)
                pdf.set_text_color(8, 145, 178)
                pdf.set_x(20)
                pdf.cell(6, 6.5, "-", ln=0)
                pdf.set_font("Helvetica", "", 10)
                pdf.set_text_color(30, 41, 59)
                pdf.set_x(26)
                pdf.multi_cell(164, 6.5, content)
                pdf.ln(1)
            else:
                pdf.set_font("Helvetica", "", 10)
                pdf.set_text_color(30, 41, 59)
                pdf.set_x(20)
                pdf.multi_cell(170, 6.5, content)
                pdf.ln(2.5)
    else:
        pdf.set_font("Helvetica", "", 10)
        pdf.set_x(20)
        pdf.multi_cell(170, 6.5, summary)

    buf = io.BytesIO(pdf.output())
    buf.seek(0)
    return buf
