#!/usr/bin/env python3
"""
Generate the redesigned project dossier PDF for “Stateless as Wind”.

The script reads `main-content.txt` to keep the narrative content in one place,
adds improved typography and backgrounds, fixes the missing Persian original
title by embedding a Unicode-capable font, and exports a v2 PDF with enhanced
section styling inspired by `EXAMPLE.pdf`.
"""

from __future__ import annotations

import unicodedata
from collections import OrderedDict
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, StyleSheet1
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    ListFlowable,
    ListItem,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parent
FONT_DIR = ROOT / "assets" / "fonts"
SOURCE_TXT = ROOT / "main-content.txt"
OUTPUT_PDF = ROOT / "stateless-as-wind-cataloge-v2.pdf"

THEME = {
    "background": colors.HexColor("#eef2f6"),
    "panel": colors.white,
    "primary": colors.HexColor("#1d3557"),
    "primary_light": colors.HexColor("#457b9d"),
    "accent": colors.HexColor("#e29578"),
    "accent_light": colors.HexColor("#f4a261"),
    "muted": colors.HexColor("#5c677d"),
    "rule": colors.HexColor("#dee3eb"),
}


def register_fonts() -> None:
    """Register the custom fonts used throughout the document."""
    pdfmetrics.registerFont(TTFont("NotoSans", str(FONT_DIR / "NotoSans-Regular.ttf")))
    pdfmetrics.registerFont(TTFont("NotoSans-Bold", str(FONT_DIR / "NotoSans-Bold.ttf")))
    pdfmetrics.registerFont(TTFont("NotoSans-Italic", str(FONT_DIR / "NotoSans-Italic.ttf")))
    pdfmetrics.registerFont(
        TTFont("NotoNaskhArabic", str(FONT_DIR / "NotoNaskhArabic-Regular.ttf"))
    )
    registerFontFamily(
        "NotoSans",
        normal="NotoSans",
        bold="NotoSans-Bold",
        italic="NotoSans-Italic",
        boldItalic="NotoSans-Bold",
    )


def prepare_rtl(text: str) -> str:
    """Reshape Arabic/Persian text for correct right-to-left rendering."""
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)


def parse_content() -> Tuple[List[str], "OrderedDict[str, List[str]]"]:
    """Split the plain-text source into cover data and ordered sections."""
    raw_text = SOURCE_TXT.read_text(encoding="utf-8")
    normalized = unicodedata.normalize("NFKC", raw_text)

    heading_map = OrderedDict(
        [
            ("General information", "General Information"),
            ("Contact", "Contact"),
            ("Logline", "Logline"),
            ("Synopsis", "Synopsis"),
            ("Artistic Approach", "Artistic Approach"),
            ("Director's Notes", "Director's Notes"),
            ("Producer's Note", "Producer's Note"),
            ("Finance Plan", "Finance Plan"),
            ("Outlook & Distribution", "Outlook & Distribution"),
            ("Biography", "Biography"),
            ("Filmography", "Filmography"),
            ("Festivals", "Festivals"),
            ("Awards", "Awards"),
            ("TV Broadcast", "TV Broadcast"),
            ("Links to Previous movie", "Links to Previous Movie"),
        ]
    )
    sections: "OrderedDict[str, List[str]]" = OrderedDict(
        (name, []) for name in heading_map.values()
    )

    cover_lines: List[str] = []
    current_section = "Cover"
    pending_heading: str | None = None

    for raw_line in normalized.splitlines():
        line = raw_line.strip()
        if not line:
            if current_section == "Cover":
                cover_lines.append("")
            else:
                sections[current_section].append("")
            continue

        # Skip lone page numbers copied from the PDF extraction.
        if line.isdigit():
            continue

        line_key = line.rstrip(":").lower()
        matched_heading = False
        for candidate, canonical in heading_map.items():
            candidate_key = candidate.rstrip(":").lower()
            if line_key == candidate_key:
                current_section = canonical
                matched_heading = True
                break
        if matched_heading:
            continue

        if current_section == "Cover":
            cover_lines.append(line)
        else:
            sections[current_section].append(line)

    return cover_lines, sections


def extract_cover_data(lines: Sequence[str]) -> Dict[str, object]:
    """Pull structured metadata for the opening spread."""
    data: Dict[str, object] = {
        "tagline": "",
        "subtitle": "",
        "original_title": "",
        "english_title": "",
        "format_label": "",
        "credits": [],
    }

    credits: List[Tuple[str, str]] = []
    pending_label: str | None = None

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        lower_line = line.lower()
        if lower_line.startswith("stateless as wind"):
            data["tagline"] = line.replace("_", "–")
            continue
        if lower_line.startswith("autobiographical documentary by"):
            data["subtitle"] = line.replace("Jala Fim", "Jala Film")
            continue
        if lower_line.startswith("original title"):
            data["original_title"] = line.split(":", 1)[1].strip()
            continue
        if lower_line.startswith("title:"):
            data["english_title"] = line.split(":", 1)[1].strip()
            continue
        if lower_line.startswith("autobiography documentary"):
            data["format_label"] = "Autobiographical Documentary"
            continue

        if pending_label:
            credits.append((pending_label, line))
            pending_label = None
            continue

        if ":" in line:
            label, value = line.split(":", 1)
            label = label.strip()
            value = value.strip()
            if not value:
                pending_label = label
            else:
                credits.append((label, value))

    data["credits"] = credits
    return data


def key_value_table(
    pairs: Sequence[Tuple[str, str]],
    width: float,
    label_style: ParagraphStyle,
    value_style: ParagraphStyle,
    zebra: bool = False,
) -> Table:
    """Create a two-column key/value table with consistent styling."""
    data = [
        [
            Paragraph(label, label_style),
            Paragraph(value, value_style),
        ]
        for label, value in pairs
    ]

    table = Table(
        data,
        colWidths=[width * 0.32, width * 0.68],
        hAlign="LEFT",
    )

    style_cmds = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TEXTCOLOR", (0, 0), (0, -1), THEME["primary"]),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, THEME["rule"]),
        ("BOX", (0, 0), (-1, -1), 0.4, THEME["rule"]),
    ]

    if zebra:
        for idx in range(0, len(data), 2):
            style_cmds.append(
                ("BACKGROUND", (0, idx), (-1, idx), colors.Color(0.95, 0.97, 0.99))
            )

    table.setStyle(TableStyle(style_cmds))
    return table


def section_heading(title: str, width: float, styles: StyleSheet1) -> Table:
    """Build a stylised heading banner inspired by modern pitch decks."""
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


def accent_rule(width: float) -> Table:
    """Add a slim accent line to separate major cover elements."""
    table = Table(
        [[""]],
        colWidths=[width],
        rowHeights=[6],
    )
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


def callout_box(text: str, width: float, styles: StyleSheet1) -> Table:
    """Highlight short statements (logline, quotes) inside a warm panel."""
    content = Paragraph(text, styles["Callout"])
    box = Table([[content]], colWidths=[width])
    box.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), THEME["accent_light"]),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ("ROUNDING", (0, 0), (-1, -1), 12),
            ]
        )
    )
    return box


def accent_list(items: Iterable[str], styles: StyleSheet1) -> ListFlowable:
    """Create a bulleted list with themed bullets."""
    flowable_items: List[ListItem] = []
    for text in items:
        if not text.strip():
            continue
        para = Paragraph(text.strip(), styles["Body"])
        flowable_items.append(
            ListItem(
                para,
                leftPadding=12,
                bulletColor=THEME["primary_light"],
                bulletFontName="NotoSans-Bold",
                bulletFontSize=8,
            )
        )
    return ListFlowable(
        flowable_items,
        bulletType="bullet",
        start="bullet",
        bulletFontName="NotoSans-Bold",
        bulletFontSize=8,
        bulletColor=THEME["primary_light"],
    )


def links_panel(entries: Sequence[Tuple[str, str]], width: float, styles: StyleSheet1) -> Table:
    """Render a panel containing project links with live hyperlinks."""
    rows = []
    for label, url in entries:
        label_para = Paragraph(f"<b>{label}</b>", styles["Small"])
        link_para = Paragraph(f'<link href="{url}">{url}</link>', styles["Link"])
        rows.append([label_para, link_para])

    panel = Table(rows, colWidths=[width * 0.3, width * 0.7], hAlign="LEFT")
    panel.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.Color(0.94, 0.96, 1.0)),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("LINEBEFORE", (1, 0), (1, -1), 0.4, THEME["rule"]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    return panel


def build_styles() -> StyleSheet1:
    """Define custom paragraph styles used in the PDF."""
    styles = StyleSheet1()
    styles.add(
        ParagraphStyle(
            "CoverTitle",
            fontName="NotoSans-Bold",
            fontSize=32,
            leading=36,
            textColor=THEME["primary"],
            alignment=TA_LEFT,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            "CoverSubtitle",
            fontName="NotoSans",
            fontSize=14,
            leading=18,
            textColor=THEME["muted"],
            alignment=TA_LEFT,
            spaceAfter=14,
        )
    )
    styles.add(
        ParagraphStyle(
            "CoverMetaLabel",
            fontName="NotoSans-Bold",
            fontSize=9,
            leading=11,
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
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            "CoverOriginalTitle",
            fontName="NotoNaskhArabic",
            fontSize=20,
            leading=26,
            textColor=THEME["primary_light"],
            alignment=TA_RIGHT,
            spaceAfter=10,
        )
    )
    styles.add(
        ParagraphStyle(
            "Body",
            fontName="NotoSans",
            fontSize=10.5,
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
            leading=11,
            textColor=THEME["primary"],
            alignment=TA_LEFT,
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            "Link",
            fontName="NotoSans",
            fontSize=9,
            leading=11,
            textColor=THEME["primary_light"],
            underline=True,
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
            "KeyValueLabel",
            fontName="NotoSans-Bold",
            fontSize=10,
            leading=12,
            textColor=THEME["primary"],
            alignment=TA_LEFT,
        )
    )
    styles.add(
        ParagraphStyle(
            "KeyValueValue",
            fontName="NotoSans",
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#232b3a"),
            alignment=TA_LEFT,
        )
    )
    styles.add(
        ParagraphStyle(
            "PersianLabel",
            parent=styles["KeyValueLabel"],
            alignment=TA_RIGHT,
        )
    )
    styles.add(
        ParagraphStyle(
            "PersianValue",
            fontName="NotoNaskhArabic",
            fontSize=18,
            leading=22,
            textColor=THEME["primary_light"],
            alignment=TA_RIGHT,
        )
    )
    return styles


def draw_background(canvas, doc) -> None:
    """Custom background with header band, rounded panel, and footer details."""
    width, height = A4
    canvas.saveState()

    canvas.setFillColor(THEME["background"])
    canvas.rect(0, 0, width, height, fill=1, stroke=0)

    panel_margin = 24
    panel_width = width - 2 * panel_margin
    panel_height = height - 2 * panel_margin
    canvas.setFillColor(THEME["panel"])
    canvas.roundRect(
        panel_margin,
        panel_margin,
        panel_width,
        panel_height,
        18,
        fill=1,
        stroke=0,
    )

    # Accent shapes for a subtle layered effect.
    canvas.setFillColor(colors.Color(0.89, 0.93, 0.99))
    canvas.circle(width - 90, height - 40, 90, stroke=0, fill=1)
    canvas.setFillColor(colors.Color(0.96, 0.91, 0.84))
    canvas.circle(70, height - 120, 55, stroke=0, fill=1)

    header_height = 46
    header_y = height - panel_margin - header_height
    canvas.setFillColor(THEME["primary"])
    canvas.roundRect(
        panel_margin + 12,
        header_y,
        panel_width - 24,
        header_height,
        12,
        fill=1,
        stroke=0,
    )

    canvas.setFillColor(colors.white)
    canvas.setFont("NotoSans-Bold", 14)
    canvas.drawString(panel_margin + 36, header_y + header_height / 2 + 4, "Stateless as Wind | Project Dossier")

    canvas.setFont("NotoSans", 9)
    canvas.setFillColor(colors.white)
    canvas.drawRightString(
        width - panel_margin - 36,
        header_y + header_height / 2 + 4,
        "Creative Documentary Pitch",
    )

    # Footer with page number.
    canvas.setFont("NotoSans", 9)
    canvas.setFillColor(THEME["muted"])
    canvas.drawString(panel_margin + 18, panel_margin + 16, "Jala Film Production · Confidential Draft")
    canvas.drawRightString(width - panel_margin - 18, panel_margin + 16, f"Page {doc.page}")

    canvas.restoreState()


def coalesce_paragraphs(lines: Sequence[str]) -> List[str]:
    """Group consecutive non-empty lines into paragraphs separated by blanks."""
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


def main() -> None:
    register_fonts()
    styles = build_styles()

    cover_lines, sections = parse_content()
    cover_data = extract_cover_data(cover_lines)

    doc = BaseDocTemplate(
        str(OUTPUT_PDF),
        pagesize=A4,
        leftMargin=72,
        rightMargin=72,
        topMargin=150,
        bottomMargin=80,
    )

    frame = Frame(
        doc.leftMargin,
        doc.bottomMargin,
        doc.width,
        doc.height,
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
    )

    doc.addPageTemplates(PageTemplate(id="main", frames=[frame], onPage=draw_background))

    story: List[object] = []

    # --- Cover Spread -----------------------------------------------------
    story.append(Spacer(1, 12))
    if cover_data["tagline"]:
        story.append(Paragraph(str(cover_data["tagline"]), styles["CoverSubtitle"]))
    story.append(Paragraph("Stateless as Wind", styles["CoverTitle"]))
    if cover_data["subtitle"]:
        story.append(Paragraph(str(cover_data["subtitle"]), styles["CoverSubtitle"]))
    story.append(accent_rule(doc.width))
    story.append(Spacer(1, 16))

    story.append(Paragraph("Original Title", styles["CoverMetaLabel"]))
    if cover_data["original_title"]:
        story.append(
            Paragraph(
                prepare_rtl(str(cover_data["original_title"])),
                styles["CoverOriginalTitle"],
            )
        )

    if cover_data["english_title"]:
        story.append(Paragraph("International Title", styles["CoverMetaLabel"]))
        story.append(
            Paragraph(str(cover_data["english_title"]), styles["CoverMetaValue"])
        )

    if cover_data["format_label"]:
        story.append(Paragraph("Format", styles["CoverMetaLabel"]))
        story.append(Paragraph(str(cover_data["format_label"]), styles["CoverMetaValue"]))

    credits_pairs: List[Tuple[str, str]] = []
    for label, value in cover_data["credits"]:
        if not value:
            continue
        if label.lower().startswith("siret"):
            value = value.replace(" ", "\u00a0")
        credits_pairs.append((label, value))

    if credits_pairs:
        story.append(Spacer(1, 8))
        story.append(
            key_value_table(
                credits_pairs,
                doc.width,
                styles["KeyValueLabel"],
                styles["KeyValueValue"],
            )
        )

    story.append(Spacer(1, 18))

    # --- General Information ---------------------------------------------
    general_pairs = []
    for line in sections.get("General Information", []):
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        general_pairs.append((key.strip(), value.strip()))

    if general_pairs:
        story.append(section_heading("General Information", doc.width, styles))
        story.append(Spacer(1, 8))
        story.append(
            key_value_table(
                general_pairs,
                doc.width,
                styles["KeyValueLabel"],
                styles["KeyValueValue"],
                zebra=True,
            )
        )

    # --- Contact ----------------------------------------------------------
    contact_lines = [line for line in sections.get("Contact", []) if line.strip()]
    if contact_lines:
        story.append(Spacer(1, 18))
        story.append(section_heading("Contact", doc.width, styles))
        story.append(Spacer(1, 8))
        for entry in contact_lines:
            story.append(Paragraph(entry.strip(), styles["Body"]))

    # --- Logline ----------------------------------------------------------
    logline_lines = [line for line in sections.get("Logline", []) if line.strip()]
    if logline_lines:
        logline_text = " ".join(logline_lines).strip()
        story.append(Spacer(1, 24))
        story.append(section_heading("Logline", doc.width, styles))
        story.append(Spacer(1, 10))
        story.append(callout_box(logline_text, doc.width, styles))

    # --- Synopsis ---------------------------------------------------------
    synopsis_lines = sections.get("Synopsis", [])
    if synopsis_lines:
        story.append(Spacer(1, 24))
        story.append(section_heading("Synopsis", doc.width, styles))
        story.append(Spacer(1, 10))
        for paragraph_text in synopsis_lines:
            cleaned = paragraph_text.strip()
            if not cleaned:
                continue
            story.append(Paragraph(cleaned, styles["Body"]))

    # --- Artistic Approach ------------------------------------------------
    artistic_lines = sections.get("Artistic Approach", [])
    if artistic_lines:
        story.append(Spacer(1, 24))
        story.append(section_heading("Artistic Approach", doc.width, styles))
        story.append(Spacer(1, 10))
        paragraphs = coalesce_paragraphs(artistic_lines)
        for text in paragraphs:
            story.append(Paragraph(text, styles["Body"]))

    # --- Director's Notes -------------------------------------------------
    director_lines = sections.get("Director's Notes", [])
    if director_lines:
        story.append(Spacer(1, 24))
        story.append(section_heading("Director’s Notes", doc.width, styles))
        story.append(Spacer(1, 10))
        paragraphs = coalesce_paragraphs(director_lines)
        for text in paragraphs:
            story.append(Paragraph(text, styles["Body"]))

    # --- Producer's Note --------------------------------------------------
    producer_lines = [line for line in sections.get("Producer's Note", []) if line]
    if producer_lines:
        story.append(Spacer(1, 24))
        story.append(section_heading("Producer’s Note", doc.width, styles))
        story.append(Spacer(1, 6))
        story.append(accent_list(producer_lines, styles))

    # --- Finance Plan -----------------------------------------------------
    finance_lines = sections.get("Finance Plan", [])
    if finance_lines:
        story.append(Spacer(1, 24))
        story.append(section_heading("Finance Plan", doc.width, styles))
        story.append(Spacer(1, 10))
        paragraphs = coalesce_paragraphs(finance_lines)
        for text in paragraphs:
            story.append(Paragraph(text, styles["Body"]))

    # --- Outlook & Distribution ------------------------------------------
    outlook_lines = sections.get("Outlook & Distribution", [])
    if outlook_lines:
        story.append(Spacer(1, 24))
        story.append(section_heading("Outlook & Distribution", doc.width, styles))
        story.append(Spacer(1, 10))
        paragraphs = coalesce_paragraphs(outlook_lines)
        for text in paragraphs:
            story.append(Paragraph(text, styles["Body"]))

    # --- Biography --------------------------------------------------------
    bio_lines = sections.get("Biography", [])
    if bio_lines:
        story.append(Spacer(1, 24))
        story.append(section_heading("Biography", doc.width, styles))
        story.append(Spacer(1, 10))
        paragraphs = coalesce_paragraphs(bio_lines)
        for idx, text in enumerate(paragraphs):
            style = styles["Body"]
            if idx == 0:
                style = styles["BodyCenter"]
            story.append(Paragraph(text, style))

    # --- Filmography ------------------------------------------------------
    film_lines = sections.get("Filmography", [])
    if film_lines:
        story.append(Spacer(1, 24))
        story.append(section_heading("Filmography", doc.width, styles))
        story.append(Spacer(1, 10))
        cleaned = [line for line in film_lines if line.strip()]
        if cleaned:
            header = cleaned[0]
            story.append(Paragraph(header, styles["Small"]))
            story.append(Spacer(1, 6))
            story.append(accent_list(cleaned[1:], styles))

    # --- Festivals --------------------------------------------------------
    festivals = sections.get("Festivals", [])
    if festivals:
        story.append(Spacer(1, 24))
        story.append(section_heading("Festival History", doc.width, styles))
        story.append(Spacer(1, 8))
        story.append(accent_list(festivals, styles))

    # --- Awards -----------------------------------------------------------
    awards = sections.get("Awards", [])
    if awards:
        story.append(Spacer(1, 24))
        story.append(section_heading("Awards", doc.width, styles))
        story.append(Spacer(1, 8))
        story.append(accent_list(awards, styles))

    # --- TV Broadcast -----------------------------------------------------
    tv_lines = sections.get("TV Broadcast", [])
    if tv_lines:
        story.append(Spacer(1, 24))
        story.append(section_heading("Broadcast", doc.width, styles))
        story.append(Spacer(1, 8))
        for text in tv_lines:
            if text.strip():
                story.append(Paragraph(text.strip(), styles["Body"]))

    # --- Links ------------------------------------------------------------
    links_section = sections.get("Links to Previous Movie", [])
    if links_section:
        story.append(Spacer(1, 24))
        story.append(section_heading("Screeners & Materials", doc.width, styles))
        story.append(Spacer(1, 10))

        entries: List[Tuple[str, str]] = []
        pending_label = None
        for line in links_section:
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
            story.append(links_panel(entries, doc.width, styles))

    doc.build(story)
    print(f"Created {OUTPUT_PDF.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
