#!/usr/bin/env python3
"""
Restructure `Original title.docx` and export a styled PDF version.

The layout keeps the narrative order intact, highlights the original title
in its own section on the first page, embeds the requested cover image, and
applies a restrained, professional design for comfortable reading.
"""

from __future__ import annotations

import unicodedata
from collections import OrderedDict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import arabic_reshaper
from bidi.algorithm import get_display
from docx import Document
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, StyleSheet1
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    ListFlowable,
    ListItem,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parent
DOCX_PATH = ROOT / "Original title.docx"
OUTPUT_PDF = ROOT / "Original title.pdf"
PHOTO_PATH = ROOT / "assets" / "photos" / "photo01.png"
FONT_DIR = ROOT / "assets" / "fonts"


THEME = {
    "background": colors.HexColor("#f4f6f9"),
    "panel": colors.white,
    "primary": colors.HexColor("#1d3557"),
    "accent": colors.HexColor("#457b9d"),
    "muted": colors.HexColor("#5c677d"),
    "rule": colors.HexColor("#d7dde7"),
}


def register_fonts() -> None:
    """Register the custom fonts used in the PDF."""
    pdfmetrics.registerFont(TTFont("NotoSans", str(FONT_DIR / "NotoSans-Regular.ttf")))
    pdfmetrics.registerFont(TTFont("NotoSans-Bold", str(FONT_DIR / "NotoSans-Bold.ttf")))
    pdfmetrics.registerFont(TTFont("NotoSans-Italic", str(FONT_DIR / "NotoSans-Italic.ttf")))
    pdfmetrics.registerFont(
        TTFont("NotoNaskhArabic", str(FONT_DIR / "NotoNaskhArabic-Regular.ttf"))
    )


def build_styles() -> StyleSheet1:
    """Define paragraph styles for the document."""
    styles = StyleSheet1()

    styles.add(
        ParagraphStyle(
            "CoverTitle",
            fontName="NotoSans-Bold",
            fontSize=30,
            leading=34,
            textColor=THEME["primary"],
            alignment=TA_LEFT,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            "CoverSubtitle",
            fontName="NotoSans",
            fontSize=13,
            leading=18,
            textColor=THEME["muted"],
            alignment=TA_LEFT,
            spaceAfter=10,
        )
    )
    styles.add(
        ParagraphStyle(
            "CoverMetaLabel",
            fontName="NotoSans-Bold",
            fontSize=10,
            leading=12,
            textColor=THEME["muted"],
            alignment=TA_LEFT,
            spaceAfter=2,
        )
    )
    styles.add(
        ParagraphStyle(
            "CoverMetaValue",
            fontName="NotoSans",
            fontSize=12,
            leading=16,
            textColor=THEME["primary"],
            alignment=TA_LEFT,
            spaceAfter=12,
        )
    )
    styles.add(
        ParagraphStyle(
            "CoverOriginal",
            fontName="NotoNaskhArabic",
            fontSize=24,
            leading=28,
            textColor=THEME["accent"],
            alignment=TA_RIGHT,
            spaceAfter=10,
        )
    )
    styles.add(
        ParagraphStyle(
            "SectionHeading",
            fontName="NotoSans-Bold",
            fontSize=13,
            leading=16,
            textColor=colors.white,
            alignment=TA_LEFT,
        )
    )
    styles.add(
        ParagraphStyle(
            "Body",
            fontName="NotoSans",
            fontSize=10.8,
            leading=14.5,
            textColor=colors.HexColor("#1f2533"),
            alignment=TA_JUSTIFY,
            spaceAfter=10,
        )
    )
    styles.add(
        ParagraphStyle(
            "BodyCenter",
            parent=styles["Body"],
            alignment=TA_CENTER,
        )
    )
    styles.add(
        ParagraphStyle(
            "Small",
            fontName="NotoSans",
            fontSize=9,
            leading=12,
            textColor=THEME["primary"],
            alignment=TA_LEFT,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            "Link",
            fontName="NotoSans",
            fontSize=9,
            leading=12,
            textColor=THEME["accent"],
            alignment=TA_LEFT,
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            "Callout",
            fontName="NotoSans-Italic",
            fontSize=11.5,
            leading=16,
            textColor=colors.white,
            alignment=TA_JUSTIFY,
        )
    )
    return styles


def prepare_rtl(text: str) -> str:
    """Reshape Persian/Arabic text for correct display."""
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)


def section_heading(title: str, width: float, styles: StyleSheet1) -> Table:
    """Stylised heading bar for each section."""
    heading = Paragraph(title.upper(), styles["SectionHeading"])
    table = Table([[heading]], colWidths=[width], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), THEME["primary"]),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return table


def callout_box(text: str, width: float, styles: StyleSheet1) -> Table:
    """Warm-toned panel for the logline."""
    paragraph = Paragraph(text, styles["Callout"])
    box = Table([[paragraph]], colWidths=[width])
    box.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), THEME["accent"]),
                ("LEFTPADDING", (0, 0), (-1, -1), 14),
                ("RIGHTPADDING", (0, 0), (-1, -1), 14),
                ("TOPPADDING", (0, 0), (-1, -1), 14),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
                ("ROUNDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    return box


def accent_rule(width: float) -> Table:
    table = Table([[""]], colWidths=[width], rowHeights=[4])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), THEME["accent"]),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return table


def key_value_table(
    pairs: Sequence[Tuple[str, str]],
    width: float,
    label_style: ParagraphStyle,
    value_style: ParagraphStyle,
) -> Table:
    data = [[Paragraph(label, label_style), Paragraph(value, value_style)] for label, value in pairs]
    table = Table(data, colWidths=[width * 0.35, width * 0.65])
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("INNERGRID", (0, 0), (-1, -1), 0.3, THEME["rule"]),
                ("BOX", (0, 0), (-1, -1), 0.4, THEME["rule"]),
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def accent_list(items: Iterable[str], styles: StyleSheet1) -> ListFlowable:
    flowables: List[ListItem] = []
    for item in items:
        stripped = item.strip()
        if not stripped:
            continue
        flowables.append(
            ListItem(
                Paragraph(stripped, styles["Body"]),
                bulletColor=THEME["accent"],
                bulletFontName="NotoSans-Bold",
                bulletFontSize=8,
                leftIndent=12,
                leftPadding=4,
            )
        )
    return ListFlowable(flowables, bulletType="bullet")


def links_panel(entries: Sequence[Tuple[str, str]], width: float, styles: StyleSheet1) -> Table:
    rows = []
    for label, url in entries:
        label_para = Paragraph(f"<b>{label}</b>", styles["Small"])
        link_para = Paragraph(f'<link href="{url}">{url}</link>', styles["Link"])
        rows.append([label_para, link_para])
    table = Table(rows, colWidths=[width * 0.35, width * 0.65])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.Color(0.93, 0.96, 1.0)),
                ("BOX", (0, 0), (-1, -1), 0.4, THEME["rule"]),
                ("LINEBEFORE", (1, 0), (1, -1), 0.35, THEME["rule"]),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    return table


def draw_background(canvas, doc) -> None:
    """Light background with header band and footer page number."""
    width, height = A4
    canvas.saveState()

    # Overall background
    canvas.setFillColor(THEME["background"])
    canvas.rect(0, 0, width, height, fill=1, stroke=0)

    # Central panel
    margin = 36
    canvas.setFillColor(THEME["panel"])
    canvas.roundRect(
        margin,
        margin,
        width - 2 * margin,
        height - 2 * margin,
        14,
        fill=1,
        stroke=0,
    )

    # Header band
    band_height = 44
    canvas.setFillColor(THEME["primary"])
    canvas.roundRect(
        margin + 10,
        height - margin - band_height,
        width - 2 * margin - 20,
        band_height,
        10,
        fill=1,
        stroke=0,
    )
    canvas.setFont("NotoSans-Bold", 12)
    canvas.setFillColor(colors.white)
    canvas.drawString(margin + 28, height - margin - band_height / 2 + 3, "STATLESS AS WIND · PROJECT DOSSIER")
    canvas.setFont("NotoSans", 8.5)
    canvas.drawRightString(
        width - margin - 28,
        height - margin - band_height / 2 + 3,
        "Creative Documentary",
    )

    # Footer
    canvas.setFont("NotoSans", 9)
    canvas.setFillColor(THEME["muted"])
    canvas.drawString(margin + 14, margin - 14, "Jala Film Production · Confidential Draft")
    canvas.drawRightString(width - margin - 14, margin - 14, f"Page {doc.page}")

    canvas.restoreState()


def load_doc_lines(path: Path) -> List[str]:
    """Read the DOCX paragraphs into a normalized list of strings."""
    document = Document(path)
    lines: List[str] = []
    for para in document.paragraphs:
        text = unicodedata.normalize("NFKC", para.text)
        lines.append(text)
    return lines


def parse_content(lines: Sequence[str]) -> Tuple[List[str], "OrderedDict[str, List[str]]"]:
    """Split DOCX lines into cover metadata and section content."""
    heading_map = OrderedDict(
        [
            ("general information", "General Information"),
            ("contact", "Contact"),
            ("logline", "Logline"),
            ("synopsis", "Synopsis"),
            ("artistic approach", "Artistic Approach"),
            ("director's notes", "Director's Notes"),
            ("director’s notes", "Director's Notes"),
            ("producer's note", "Producer's Note"),
            ("producer’s note", "Producer's Note"),
            ("finance plan", "Finance Plan"),
            ("outlook & distribution", "Outlook & Distribution"),
            ("biography", "Biography"),
            ("filmography", "Filmography"),
            ("festivals", "Festivals"),
            ("awards", "Awards"),
            ("tv broadcast", "TV Broadcast"),
            ("links to previous movie", "Links to Previous Movie"),
        ]
    )

    sections: "OrderedDict[str, List[str]]" = OrderedDict((v, []) for v in heading_map.values())
    cover_lines: List[str] = []
    current_section = "Cover"

    for raw_line in lines:
        line = raw_line.strip()

        if not line:
            if current_section == "Cover":
                cover_lines.append("")
            else:
                sections[current_section].append("")
            continue

        # Remove trailing colon for matching.
        key = line.rstrip(":").lower()
        if key in heading_map:
            current_section = heading_map[key]
            continue

        if current_section == "Cover":
            cover_lines.append(line)
        else:
            sections[current_section].append(line)

    return cover_lines, sections


def extract_cover_data(lines: Sequence[str]) -> Dict[str, object]:
    """Turn the free-form cover text into structured fields."""
    data: Dict[str, object] = {
        "tagline": "",
        "subtitle": "",
        "original_title": "",
        "english_title": "",
        "format_label": "",
        "credits": [],
    }

    credits: List[Tuple[str, str]] = []
    pending_label: Optional[str] = None

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        lowered = line.lower()
        if lowered.startswith("stateless as wind"):
            data["tagline"] = line.replace("_", "–")
            continue
        if lowered.startswith("autobiographical documentary by"):
            data["subtitle"] = line.replace("Jala Fim", "Jala Film")
            continue
        if lowered.startswith("original title"):
            parts = line.split(":", 1)
            if len(parts) == 2:
                data["original_title"] = parts[1].strip()
            continue
        if lowered.startswith("title"):
            parts = line.split(":", 1)
            if len(parts) == 2:
                data["english_title"] = parts[1].strip()
            continue
        if "autobiograph" in lowered and "documentary" in lowered:
            data["format_label"] = "Autobiographical Documentary"
            continue

        if ":" in line:
            label, value = line.split(":", 1)
            label = label.strip()
            value = value.strip()
            if value:
                credits.append((label, value))
            else:
                pending_label = label
            continue

        if pending_label:
            credits.append((pending_label, line))
            pending_label = None
        else:
            credits.append(("Note", line))

    data["credits"] = credits
    return data


def coalesce_paragraphs(lines: Sequence[str]) -> List[str]:
    """Group consecutive lines into paragraphs separated by blanks."""
    paragraphs: List[str] = []
    buffer: List[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if buffer:
                paragraphs.append(" ".join(buffer))
                buffer = []
            continue
        buffer.append(stripped)

    if buffer:
        paragraphs.append(" ".join(buffer))

    return paragraphs


def make_cover_story(
    cover_data: Dict[str, object],
    doc_width: float,
    styles: StyleSheet1,
) -> List[object]:
    story: List[object] = []
    story.append(Spacer(1, 12))

    tagline = str(cover_data.get("tagline") or "").strip()
    if tagline:
        story.append(Paragraph(tagline, styles["CoverSubtitle"]))

    english_title = str(cover_data.get("english_title") or "Stateless as Wind")
    story.append(Paragraph(english_title, styles["CoverTitle"]))

    subtitle = str(cover_data.get("subtitle") or "").strip()
    if subtitle:
        story.append(Paragraph(subtitle, styles["CoverSubtitle"]))

    story.append(accent_rule(doc_width))
    story.append(Spacer(1, 14))

    story.append(section_heading("Original Title", doc_width, styles))
    story.append(Spacer(1, 10))

    original_title = str(cover_data.get("original_title") or "").strip()
    if original_title:
        story.append(
            Paragraph(
                prepare_rtl(original_title),
                styles["CoverOriginal"],
            )
        )

    story.append(Paragraph("International Title", styles["CoverMetaLabel"]))
    story.append(Paragraph(english_title, styles["CoverMetaValue"]))

    format_label = str(cover_data.get("format_label") or "").strip()
    if format_label:
        story.append(Paragraph("Format", styles["CoverMetaLabel"]))
        story.append(Paragraph(format_label, styles["CoverMetaValue"]))

    credits_pairs: List[Tuple[str, str]] = []
    for label, value in cover_data.get("credits", []):
        value = value.strip()
        if not value:
            continue
        credits_pairs.append((label, value))

    if credits_pairs:
        story.append(Spacer(1, 6))
        story.append(
            key_value_table(
                credits_pairs,
                doc_width,
                styles["CoverMetaLabel"],
                styles["CoverMetaValue"],
            )
        )

    if PHOTO_PATH.exists():
        try:
            reader = ImageReader(str(PHOTO_PATH))
            img_width, img_height = reader.getSize()
            scale = min((doc_width * 0.9) / img_width, 360 / img_height, 1.0)
            width = img_width * scale
            height = img_height * scale
            image = Image(str(PHOTO_PATH), width=width, height=height)
            image.hAlign = "CENTER"
            story.append(Spacer(1, 18))
            story.append(image)
        except Exception as exc:  # pragma: no cover - defensive
            story.append(Paragraph(f"[Unable to load cover image: {exc}]", styles["Small"]))

    story.append(PageBreak())
    return story


def build_story(sections: "OrderedDict[str, List[str]]", doc_width: float, styles: StyleSheet1) -> List[object]:
    story: List[object] = []

    # General Information
    general_pairs: List[Tuple[str, str]] = []
    for line in sections.get("General Information", []):
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        general_pairs.append((key.strip(), value.strip()))
    if general_pairs:
        story.append(section_heading("General Information", doc_width, styles))
        story.append(Spacer(1, 10))
        story.append(
            key_value_table(
                general_pairs,
                doc_width,
                styles["Small"],
                styles["Body"],
            )
        )

    # Contact
    contact_lines = coalesce_paragraphs(sections.get("Contact", []))
    if contact_lines:
        story.append(Spacer(1, 18))
        story.append(section_heading("Contact", doc_width, styles))
        story.append(Spacer(1, 8))
        for line in contact_lines:
            story.append(Paragraph(line, styles["Body"]))

    # Logline
    logline_lines = coalesce_paragraphs(sections.get("Logline", []))
    if logline_lines:
        story.append(Spacer(1, 24))
        story.append(section_heading("Logline", doc_width, styles))
        story.append(Spacer(1, 12))
        story.append(callout_box(" ".join(logline_lines), doc_width, styles))

    # Synopsis
    synopsis_paragraphs = coalesce_paragraphs(sections.get("Synopsis", []))
    if synopsis_paragraphs:
        story.append(Spacer(1, 24))
        story.append(section_heading("Synopsis", doc_width, styles))
        story.append(Spacer(1, 10))
        for paragraph_text in synopsis_paragraphs:
            story.append(Paragraph(paragraph_text, styles["Body"]))

    # Artistic Approach
    artistic_paragraphs = coalesce_paragraphs(sections.get("Artistic Approach", []))
    if artistic_paragraphs:
        story.append(Spacer(1, 24))
        story.append(section_heading("Artistic Approach", doc_width, styles))
        story.append(Spacer(1, 10))
        for paragraph_text in artistic_paragraphs:
            story.append(Paragraph(paragraph_text, styles["Body"]))

    # Director's Notes
    director_paragraphs = coalesce_paragraphs(sections.get("Director's Notes", []))
    if director_paragraphs:
        story.append(Spacer(1, 24))
        story.append(section_heading("Director's Notes", doc_width, styles))
        story.append(Spacer(1, 10))
        for idx, paragraph_text in enumerate(director_paragraphs):
            style = styles["BodyCenter"] if idx == 0 else styles["Body"]
            story.append(Paragraph(paragraph_text, style))

    # Producer's Note
    producer_paragraphs = coalesce_paragraphs(sections.get("Producer's Note", []))
    if producer_paragraphs:
        story.append(Spacer(1, 24))
        story.append(section_heading("Producer's Note", doc_width, styles))
        story.append(Spacer(1, 10))
        for paragraph_text in producer_paragraphs:
            story.append(Paragraph(paragraph_text, styles["Body"]))

    # Finance Plan
    finance_paragraphs = coalesce_paragraphs(sections.get("Finance Plan", []))
    if finance_paragraphs:
        story.append(Spacer(1, 24))
        story.append(section_heading("Finance Plan", doc_width, styles))
        story.append(Spacer(1, 10))
        for paragraph_text in finance_paragraphs:
            story.append(Paragraph(paragraph_text, styles["Body"]))

    # Outlook & Distribution
    outlook_paragraphs = coalesce_paragraphs(sections.get("Outlook & Distribution", []))
    if outlook_paragraphs:
        story.append(Spacer(1, 24))
        story.append(section_heading("Outlook & Distribution", doc_width, styles))
        story.append(Spacer(1, 10))
        for paragraph_text in outlook_paragraphs:
            story.append(Paragraph(paragraph_text, styles["Body"]))

    # Biography
    biography_paragraphs = coalesce_paragraphs(sections.get("Biography", []))
    if biography_paragraphs:
        story.append(Spacer(1, 24))
        story.append(section_heading("Biography", doc_width, styles))
        story.append(Spacer(1, 10))
        for paragraph_text in biography_paragraphs:
            story.append(Paragraph(paragraph_text, styles["Body"]))

    # Filmography
    filmography_lines = sections.get("Filmography", [])
    if filmography_lines:
        story.append(Spacer(1, 24))
        story.append(section_heading("Filmography", doc_width, styles))
        story.append(Spacer(1, 10))
        cleaned = [line.strip() for line in filmography_lines if line.strip()]
        if cleaned:
            story.append(Paragraph(cleaned[0], styles["Small"]))
            if len(cleaned) > 1:
                story.append(Spacer(1, 6))
                story.append(accent_list(cleaned[1:], styles))

    # Festivals
    festival_lines = sections.get("Festivals", [])
    if festival_lines:
        story.append(Spacer(1, 24))
        story.append(section_heading("Festivals", doc_width, styles))
        story.append(Spacer(1, 8))
        story.append(accent_list(festival_lines, styles))

    # Awards
    award_lines = sections.get("Awards", [])
    if award_lines:
        story.append(Spacer(1, 24))
        story.append(section_heading("Awards", doc_width, styles))
        story.append(Spacer(1, 8))
        story.append(accent_list(award_lines, styles))

    # TV Broadcast
    broadcast_paragraphs = coalesce_paragraphs(sections.get("TV Broadcast", []))
    if broadcast_paragraphs:
        story.append(Spacer(1, 24))
        story.append(section_heading("TV Broadcast", doc_width, styles))
        story.append(Spacer(1, 8))
        for paragraph_text in broadcast_paragraphs:
            story.append(Paragraph(paragraph_text, styles["Body"]))

    # Links
    links_lines = sections.get("Links to Previous Movie", [])
    if links_lines:
        story.append(Spacer(1, 24))
        story.append(section_heading("Links to Previous Movie", doc_width, styles))
        story.append(Spacer(1, 10))
        entries: List[Tuple[str, str]] = []
        pending_label: Optional[str] = None
        for line in links_lines:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.endswith(":"):
                pending_label = stripped.rstrip(":")
                continue
            if pending_label:
                entries.append((pending_label, stripped))
                pending_label = None
            else:
                entries.append(("Link", stripped))
        if entries:
            story.append(links_panel(entries, doc_width, styles))

    return story


def main() -> None:
    if not DOCX_PATH.exists():
        raise FileNotFoundError(f"Missing source document: {DOCX_PATH}")

    register_fonts()
    styles = build_styles()

    lines = load_doc_lines(DOCX_PATH)
    cover_lines, sections = parse_content(lines)
    cover_data = extract_cover_data(cover_lines)

    doc = BaseDocTemplate(
        str(OUTPUT_PDF),
        pagesize=A4,
        leftMargin=72,
        rightMargin=72,
        topMargin=110,
        bottomMargin=90,
    )
    frame = Frame(
        doc.leftMargin,
        doc.bottomMargin,
        doc.width,
        doc.height,
        leftPadding=18,
        rightPadding=18,
        topPadding=18,
        bottomPadding=24,
    )
    doc.addPageTemplates(PageTemplate(id="main", frames=[frame], onPage=draw_background))

    story: List[object] = []
    story.extend(make_cover_story(cover_data, doc.width, styles))
    story.extend(build_story(sections, doc.width, styles))

    doc.build(story)
    print(f"Created {OUTPUT_PDF.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
