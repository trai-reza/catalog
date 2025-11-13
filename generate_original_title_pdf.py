#!/usr/bin/env python3
"""
Generate a restructured PDF from "Original title.docx" with professional design.
- Uses photo01.png on the first page
- Keeps content order unchanged
- Makes sections clearly separate
- Simple and professional design
"""

from __future__ import annotations

import unicodedata
from pathlib import Path
from typing import List, Optional

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
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parent
FONT_DIR = ROOT / "assets" / "fonts"
SOURCE_DOCX = ROOT / "Original title.docx"
OUTPUT_PDF = ROOT / "Original title.pdf"
PHOTO_LIBRARY = ROOT / "assets" / "photos"

THEME = {
    "background": colors.HexColor("#f5f7fa"),
    "panel": colors.white,
    "primary": colors.HexColor("#1a365d"),
    "primary_light": colors.HexColor("#2d4a6b"),
    "accent": colors.HexColor("#4299e1"),
    "accent_light": colors.HexColor("#63b3ed"),
    "muted": colors.HexColor("#718096"),
    "rule": colors.HexColor("#e2e8f0"),
    "text": colors.HexColor("#2d3748"),
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
    try:
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except Exception:
        return text


def extract_docx_content() -> List[str]:
    """Extract all paragraphs from the DOCX file."""
    doc = Document(str(SOURCE_DOCX))
    return [p.text for p in doc.paragraphs]


def parse_sections(lines: List[str]) -> dict:
    """Parse content into sections based on headings."""
    sections = {}
    current_section = None
    current_content = []
    
    section_keywords = {
        "general information": "General Information",
        "contact": "Contact",
        "logline": "Logline",
        "synopsis": "Synopsis",
        "artistic approach": "Artistic Approach",
        "visual material": "Visual Material",
        "director's notes": "Director's Notes",
        "producer's note": "Producer's Note",
        "finance plan": "Finance Plan",
        "outlook & distribution": "Outlook & Distribution",
        "biography": "Biography",
        "filmography": "Filmography",
        "festivals": "Festivals",
        "awards": "Awards",
        "tv broadcast": "TV Broadcast",
        "links to previous movie": "Links to Previous Movie",
    }
    
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            if current_section and current_content:
                current_content.append("")
            continue
        
        # Check if this line is a section heading (exact match or starts with keyword)
        found_section = False
        line_lower = line_stripped.lower().rstrip(":")
        
        for keyword, section_name in section_keywords.items():
            if line_lower == keyword or line_lower.startswith(keyword + ":"):
                # Save previous section
                if current_section and current_content:
                    sections[current_section] = current_content
                current_section = section_name
                current_content = []
                found_section = True
                break
        
        if not found_section:
            if current_section:
                current_content.append(line_stripped)
            # If we haven't found a section yet, this is cover content (but we handle cover separately)
    
    # Save last section
    if current_section and current_content:
        sections[current_section] = current_content
    
    return sections


def extract_cover_info(lines: List[str]) -> dict:
    """Extract cover information from the beginning of the document."""
    info = {
        "title": "",
        "subtitle": "",
        "original_title": "",
        "english_title": "",
        "format": "",
        "director": "",
        "production_company": "",
        "siret": "",
        "cinematographers": "",
        "editor": "",
        "sound_recordist": "",
    }
    
    # Find where "General information" starts to know where cover ends
    cover_end_idx = len(lines)
    for i, line in enumerate(lines):
        if "general information" in line.lower().strip():
            cover_end_idx = i
            break
    
    # Process only cover section
    for i, line in enumerate(lines[:cover_end_idx]):
        line_stripped = line.strip()
        if not line_stripped:
            continue
            
        line_lower = line_stripped.lower()
        
        if "stateless as wind" in line_lower and "2015" in line_stripped:
            info["title"] = line_stripped
        elif "autobiographical documentary" in line_lower:
            info["subtitle"] = line_stripped
        elif line_lower.startswith("original title:"):
            info["original_title"] = line_stripped.split(":", 1)[1].strip() if ":" in line_stripped else ""
        elif line_lower.startswith("title:") and not info["english_title"]:
            info["english_title"] = line_stripped.split(":", 1)[1].strip() if ":" in line_stripped else ""
        elif ("autobiography documentary" in line_lower or "autobiographical documentary" in line_lower) and not info["format"]:
            info["format"] = line_stripped
        elif line_lower.startswith("director") and not info["director"]:
            info["director"] = line_stripped.split(":", 1)[1].strip() if ":" in line_stripped else line_stripped
        elif "production company" in line_lower:
            if ":" in line_stripped:
                info["production_company"] = line_stripped.split(":", 1)[1].strip()
            elif i + 1 < cover_end_idx and lines[i + 1].strip():
                info["production_company"] = lines[i + 1].strip()
        elif "jala film" in line_lower and not info["production_company"]:
            info["production_company"] = line_stripped
        elif line_lower.startswith("siret:"):
            info["siret"] = line_stripped.split(":", 1)[1].strip() if ":" in line_stripped else ""
        elif line_lower.startswith("cinematographer") and not info["cinematographers"]:
            info["cinematographers"] = line_stripped.split(":", 1)[1].strip() if ":" in line_stripped else line_stripped
        elif line_lower.startswith("editor:") and not info["editor"]:
            info["editor"] = line_stripped.split(":", 1)[1].strip() if ":" in line_stripped else ""
        elif line_lower.startswith("sound recordist") and not info["sound_recordist"]:
            info["sound_recordist"] = line_stripped.split(":", 1)[1].strip() if ":" in line_stripped else ""
    
    return info


def section_heading(title: str, width: float, styles: StyleSheet1) -> Table:
    """Create a styled section heading."""
    heading = Paragraph(title.upper(), styles["SectionHeading"])
    table = Table([[heading]], colWidths=[width], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), THEME["primary"]),
                ("LEFTPADDING", (0, 0), (-1, -1), 16),
                ("RIGHTPADDING", (0, 0), (-1, -1), 16),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    return table


def accent_rule(width: float) -> Table:
    """Add a decorative accent line."""
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


def build_styles() -> StyleSheet1:
    """Define custom paragraph styles."""
    styles = StyleSheet1()
    
    styles.add(
        ParagraphStyle(
            "CoverTitle",
            fontName="NotoSans-Bold",
            fontSize=28,
            leading=34,
            textColor=THEME["primary"],
            alignment=TA_LEFT,
            spaceAfter=8,
        )
    )
    
    styles.add(
        ParagraphStyle(
            "CoverSubtitle",
            fontName="NotoSans",
            fontSize=13,
            leading=17,
            textColor=THEME["muted"],
            alignment=TA_LEFT,
            spaceAfter=12,
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
            fontSize=11,
            leading=15,
            textColor=THEME["text"],
            alignment=TA_LEFT,
            spaceAfter=8,
        )
    )
    
    styles.add(
        ParagraphStyle(
            "CoverOriginalTitle",
            fontName="NotoNaskhArabic",
            fontSize=18,
            leading=24,
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
            leading=15,
            textColor=THEME["text"],
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
            textColor=THEME["text"],
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
            underline=True,
            alignment=TA_LEFT,
            spaceAfter=6,
        )
    )
    
    styles.add(
        ParagraphStyle(
            "SectionHeading",
            fontName="NotoSans-Bold",
            fontSize=12,
            leading=15,
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
            textColor=THEME["text"],
            alignment=TA_LEFT,
        )
    )
    
    return styles


def draw_background(canvas, doc) -> None:
    """Draw custom background with header and footer."""
    width, height = A4
    canvas.saveState()
    
    # Background
    canvas.setFillColor(THEME["background"])
    canvas.rect(0, 0, width, height, fill=1, stroke=0)
    
    # Main panel
    panel_margin = 20
    panel_width = width - 2 * panel_margin
    panel_height = height - 2 * panel_margin
    canvas.setFillColor(THEME["panel"])
    canvas.roundRect(
        panel_margin,
        panel_margin,
        panel_width,
        panel_height,
        12,
        fill=1,
        stroke=0,
    )
    
    # Subtle accent circle
    canvas.setFillColor(colors.Color(0.92, 0.95, 0.98))
    canvas.circle(width - 60, height - 50, 50, stroke=0, fill=1)
    
    # Footer
    canvas.setFont("NotoSans", 8)
    canvas.setFillColor(THEME["muted"])
    canvas.drawString(
        panel_margin + 18,
        panel_margin + 12,
        "Jala Film Production"
    )
    canvas.drawRightString(
        width - panel_margin - 18,
        panel_margin + 12,
        f"Page {doc.page}"
    )
    
    canvas.restoreState()


def make_image_flowable(image_path: Path, max_width: float, max_height: float) -> Optional[Image]:
    """Create a scaled image flowable."""
    if not image_path.exists():
        print(f"Warning: Image not found: {image_path.name}")
        return None
    
    try:
        reader = ImageReader(str(image_path))
        width, height = reader.getSize()
    except Exception as exc:
        print(f"Error reading {image_path.name}: {exc}")
        return None
    
    if width <= 0 or height <= 0:
        return None
    
    scale = min(max_width / width, max_height / height, 1.0)
    target_width = width * scale
    target_height = height * scale
    
    image = Image(str(image_path), width=target_width, height=target_height)
    image.hAlign = "CENTER"
    return image


def coalesce_paragraphs(lines: List[str]) -> List[str]:
    """Group consecutive non-empty lines into paragraphs."""
    paragraphs = []
    buffer = []
    
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
    
    # Extract content from DOCX
    lines = extract_docx_content()
    sections = parse_sections(lines)
    cover_info = extract_cover_info(lines)
    
    # Create PDF document
    doc = BaseDocTemplate(
        str(OUTPUT_PDF),
        pagesize=A4,
        leftMargin=60,
        rightMargin=60,
        topMargin=100,
        bottomMargin=70,
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
    
    story = []
    
    # === FIRST PAGE: Cover with photo01.png ===
    story.append(Spacer(1, 20))
    
    # Title
    if cover_info["title"]:
        story.append(Paragraph(cover_info["title"], styles["CoverSubtitle"]))
    story.append(Paragraph("Stateless as Wind", styles["CoverTitle"]))
    if cover_info["subtitle"]:
        story.append(Paragraph(cover_info["subtitle"], styles["CoverSubtitle"]))
    
    story.append(Spacer(1, 12))
    story.append(accent_rule(doc.width))
    story.append(Spacer(1, 16))
    
    # Original Title
    if cover_info["original_title"]:
        story.append(Paragraph("Original Title", styles["CoverMetaLabel"]))
        story.append(
            Paragraph(
                prepare_rtl(cover_info["original_title"]),
                styles["CoverOriginalTitle"],
            )
        )
    
    # English Title
    if cover_info["english_title"]:
        story.append(Paragraph("Title", styles["CoverMetaLabel"]))
        story.append(Paragraph(cover_info["english_title"], styles["CoverMetaValue"]))
    
    # Format
    if cover_info["format"]:
        story.append(Paragraph("Format", styles["CoverMetaLabel"]))
        story.append(Paragraph(cover_info["format"], styles["CoverMetaValue"]))
    
    # Credits
    if cover_info["director"]:
        story.append(Paragraph("Director / Writer / Producer", styles["CoverMetaLabel"]))
        story.append(Paragraph(cover_info["director"], styles["CoverMetaValue"]))
    
    if cover_info["production_company"]:
        story.append(Paragraph("Production Company", styles["CoverMetaLabel"]))
        story.append(Paragraph(cover_info["production_company"], styles["CoverMetaValue"]))
    
    if cover_info["siret"]:
        story.append(Paragraph("SIRET", styles["CoverMetaLabel"]))
        story.append(Paragraph(cover_info["siret"], styles["CoverMetaValue"]))
    
    if cover_info["cinematographers"]:
        story.append(Paragraph("Cinematographers", styles["CoverMetaLabel"]))
        story.append(Paragraph(cover_info["cinematographers"], styles["CoverMetaValue"]))
    
    if cover_info["editor"]:
        story.append(Paragraph("Editor", styles["CoverMetaLabel"]))
        story.append(Paragraph(cover_info["editor"], styles["CoverMetaValue"]))
    
    if cover_info["sound_recordist"]:
        story.append(Paragraph("Sound Recordist", styles["CoverMetaLabel"]))
        story.append(Paragraph(cover_info["sound_recordist"], styles["CoverMetaValue"]))
    
    # Add photo01.png on first page
    story.append(Spacer(1, 20))
    photo01_path = PHOTO_LIBRARY / "photo01.png"
    image = make_image_flowable(photo01_path, doc.width * 0.9, 300)
    if image:
        story.append(image)
    
    story.append(PageBreak())
    
    # === General Information ===
    if "General Information" in sections:
        story.append(Spacer(1, 24))
        story.append(section_heading("General Information", doc.width, styles))
        story.append(Spacer(1, 12))
        
        general_lines = sections["General Information"]
        for line in general_lines:
            if not line.strip():
                continue
            if ":" in line:
                key, value = line.split(":", 1)
                story.append(Paragraph(f"<b>{key.strip()}:</b> {value.strip()}", styles["Body"]))
            else:
                story.append(Paragraph(line, styles["Body"]))
    
    # === Contact ===
    if "Contact" in sections:
        story.append(Spacer(1, 20))
        story.append(section_heading("Contact", doc.width, styles))
        story.append(Spacer(1, 10))
        
        for line in sections["Contact"]:
            if line.strip():
                story.append(Paragraph(line.strip(), styles["Body"]))
    
    # === Logline ===
    if "Logline" in sections:
        story.append(Spacer(1, 20))
        story.append(section_heading("Logline", doc.width, styles))
        story.append(Spacer(1, 10))
        
        logline_text = " ".join([line for line in sections["Logline"] if line.strip()])
        if logline_text:
            story.append(Paragraph(logline_text, styles["Body"]))
    
    # === Synopsis ===
    if "Synopsis" in sections:
        story.append(Spacer(1, 20))
        story.append(section_heading("Synopsis", doc.width, styles))
        story.append(Spacer(1, 10))
        
        paragraphs = coalesce_paragraphs(sections["Synopsis"])
        for para in paragraphs:
            story.append(Paragraph(para, styles["Body"]))
    
    # === Artistic Approach ===
    if "Artistic Approach" in sections:
        story.append(Spacer(1, 20))
        story.append(section_heading("Artistic Approach", doc.width, styles))
        story.append(Spacer(1, 10))
        
        paragraphs = coalesce_paragraphs(sections["Artistic Approach"])
        for para in paragraphs:
            story.append(Paragraph(para, styles["Body"]))
    
    # === Visual Material ===
    if "Visual Material" in sections:
        story.append(Spacer(1, 20))
        story.append(section_heading("Visual Material", doc.width, styles))
        story.append(Spacer(1, 10))
        
        for line in sections["Visual Material"]:
            if line.strip():
                story.append(Paragraph(line.strip(), styles["Body"]))
    
    # === Director's Notes ===
    if "Director's Notes" in sections:
        story.append(Spacer(1, 20))
        story.append(section_heading("Director's Notes", doc.width, styles))
        story.append(Spacer(1, 10))
        
        paragraphs = coalesce_paragraphs(sections["Director's Notes"])
        for para in paragraphs:
            story.append(Paragraph(para, styles["Body"]))
    
    # === Producer's Note ===
    if "Producer's Note" in sections:
        story.append(Spacer(1, 20))
        story.append(section_heading("Producer's Note", doc.width, styles))
        story.append(Spacer(1, 10))
        
        paragraphs = coalesce_paragraphs(sections["Producer's Note"])
        for para in paragraphs:
            story.append(Paragraph(para, styles["Body"]))
    
    # === Finance Plan ===
    if "Finance Plan" in sections:
        story.append(Spacer(1, 20))
        story.append(section_heading("Finance Plan", doc.width, styles))
        story.append(Spacer(1, 10))
        
        paragraphs = coalesce_paragraphs(sections["Finance Plan"])
        for para in paragraphs:
            story.append(Paragraph(para, styles["Body"]))
    
    # === Outlook & Distribution ===
    if "Outlook & Distribution" in sections:
        story.append(Spacer(1, 20))
        story.append(section_heading("Outlook & Distribution", doc.width, styles))
        story.append(Spacer(1, 10))
        
        paragraphs = coalesce_paragraphs(sections["Outlook & Distribution"])
        for para in paragraphs:
            story.append(Paragraph(para, styles["Body"]))
    
    # === Biography ===
    if "Biography" in sections:
        story.append(Spacer(1, 20))
        story.append(section_heading("Biography", doc.width, styles))
        story.append(Spacer(1, 10))
        
        paragraphs = coalesce_paragraphs(sections["Biography"])
        for para in paragraphs:
            story.append(Paragraph(para, styles["Body"]))
    
    # === Filmography ===
    if "Filmography" in sections:
        story.append(Spacer(1, 20))
        story.append(section_heading("Filmography", doc.width, styles))
        story.append(Spacer(1, 10))
        
        for line in sections["Filmography"]:
            if line.strip():
                story.append(Paragraph(line.strip(), styles["Body"]))
    
    # === Festivals ===
    if "Festivals" in sections:
        story.append(Spacer(1, 20))
        story.append(section_heading("Festivals", doc.width, styles))
        story.append(Spacer(1, 10))
        
        for line in sections["Festivals"]:
            if line.strip():
                story.append(Paragraph(line.strip(), styles["Body"]))
    
    # === Awards ===
    if "Awards" in sections:
        story.append(Spacer(1, 20))
        story.append(section_heading("Awards", doc.width, styles))
        story.append(Spacer(1, 10))
        
        for line in sections["Awards"]:
            if line.strip():
                story.append(Paragraph(line.strip(), styles["Body"]))
    
    # === TV Broadcast ===
    if "TV Broadcast" in sections:
        story.append(Spacer(1, 20))
        story.append(section_heading("TV Broadcast", doc.width, styles))
        story.append(Spacer(1, 10))
        
        for line in sections["TV Broadcast"]:
            if line.strip():
                story.append(Paragraph(line.strip(), styles["Body"]))
    
    # === Links to Previous Movie ===
    if "Links to Previous Movie" in sections:
        story.append(Spacer(1, 20))
        story.append(section_heading("Links to Previous Movie", doc.width, styles))
        story.append(Spacer(1, 10))
        
        for line in sections["Links to Previous Movie"]:
            if line.strip():
                if line.strip().startswith("http"):
                    story.append(Paragraph(f'<link href="{line.strip()}">{line.strip()}</link>', styles["Link"]))
                else:
                    story.append(Paragraph(line.strip(), styles["Body"]))
    
    # Build PDF
    doc.build(story)
    print(f"✓ Created {OUTPUT_PDF.name}")


if __name__ == "__main__":
    main()
