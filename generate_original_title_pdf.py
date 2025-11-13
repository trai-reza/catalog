#!/usr/bin/env python3
"""
Generate a professional PDF for "Stateless as Wind" from Original title.docx
with clean design and clear section separation.
"""

from pathlib import Path
import json
import arabic_reshaper
from bidi.algorithm import get_display
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
    PageTemplate,
    PageBreak,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parent
FONT_DIR = ROOT / "assets" / "fonts"
OUTPUT_PDF = ROOT / "original-title-formatted.pdf"
PHOTO_PATH = ROOT / "assets" / "photos" / "photo01.png"

# Simple and professional color scheme
THEME = {
    "background": colors.HexColor("#f5f7fa"),
    "panel": colors.white,
    "primary": colors.HexColor("#2c3e50"),
    "primary_light": colors.HexColor("#34495e"),
    "accent": colors.HexColor("#3498db"),
    "accent_light": colors.HexColor("#5dade2"),
    "muted": colors.HexColor("#7f8c8d"),
    "rule": colors.HexColor("#bdc3c7"),
}


def register_fonts():
    """Register custom fonts for the document."""
    pdfmetrics.registerFont(TTFont("NotoSans", str(FONT_DIR / "NotoSans-Regular.ttf")))
    pdfmetrics.registerFont(TTFont("NotoSans-Bold", str(FONT_DIR / "NotoSans-Bold.ttf")))
    pdfmetrics.registerFont(TTFont("NotoSans-Italic", str(FONT_DIR / "NotoSans-Italic.ttf")))
    pdfmetrics.registerFont(TTFont("NotoNaskhArabic", str(FONT_DIR / "NotoNaskhArabic-Regular.ttf")))
    registerFontFamily(
        "NotoSans",
        normal="NotoSans",
        bold="NotoSans-Bold",
        italic="NotoSans-Italic",
        boldItalic="NotoSans-Bold",
    )


def prepare_rtl(text: str) -> str:
    """Reshape Arabic/Persian text for right-to-left rendering."""
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)


def build_styles() -> StyleSheet1:
    """Create paragraph styles for the document."""
    styles = StyleSheet1()
    
    # Title style
    styles.add(ParagraphStyle(
        "Title",
        fontName="NotoSans-Bold",
        fontSize=28,
        leading=34,
        textColor=THEME["primary"],
        alignment=TA_CENTER,
        spaceAfter=12,
    ))
    
    # Subtitle style
    styles.add(ParagraphStyle(
        "Subtitle",
        fontName="NotoSans",
        fontSize=13,
        leading=18,
        textColor=THEME["muted"],
        alignment=TA_CENTER,
        spaceAfter=16,
    ))
    
    # Section heading style
    styles.add(ParagraphStyle(
        "SectionHeading",
        fontName="NotoSans-Bold",
        fontSize=14,
        leading=18,
        textColor=colors.white,
        alignment=TA_LEFT,
        spaceAfter=0,
    ))
    
    # Body text style
    styles.add(ParagraphStyle(
        "Body",
        fontName="NotoSans",
        fontSize=10,
        leading=14,
        textColor=THEME["primary_light"],
        alignment=TA_JUSTIFY,
        spaceAfter=8,
    ))
    
    # Body left-aligned style
    styles.add(ParagraphStyle(
        "BodyLeft",
        parent=styles["Body"],
        alignment=TA_LEFT,
    ))
    
    # Small text style
    styles.add(ParagraphStyle(
        "Small",
        fontName="NotoSans",
        fontSize=9,
        leading=12,
        textColor=THEME["muted"],
        alignment=TA_LEFT,
        spaceAfter=6,
    ))
    
    # Persian/Arabic text style
    styles.add(ParagraphStyle(
        "Persian",
        fontName="NotoNaskhArabic",
        fontSize=16,
        leading=22,
        textColor=THEME["accent"],
        alignment=TA_RIGHT,
        spaceAfter=8,
    ))
    
    # Label style
    styles.add(ParagraphStyle(
        "Label",
        fontName="NotoSans-Bold",
        fontSize=9,
        leading=12,
        textColor=THEME["primary"],
        alignment=TA_LEFT,
        spaceAfter=2,
    ))
    
    return styles


def section_heading(title: str, width: float, styles: StyleSheet1) -> Table:
    """Create a styled section heading banner."""
    heading = Paragraph(title.upper(), styles["SectionHeading"])
    table = Table([[heading]], colWidths=[width], hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), THEME["accent"]),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    return table


def accent_divider(width: float) -> Table:
    """Create a thin dividing line."""
    table = Table([[""]],  colWidths=[width], rowHeights=[2])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), THEME["accent_light"]),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return table


def draw_background(canvas, doc):
    """Draw a clean background with subtle styling."""
    width, height = A4
    canvas.saveState()
    
    # Background
    canvas.setFillColor(THEME["background"])
    canvas.rect(0, 0, width, height, fill=1, stroke=0)
    
    # Content panel
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
    
    # Header bar
    if doc.page > 1:  # Skip header on first page
        header_height = 36
        header_y = height - panel_margin - header_height - 8
        canvas.setFillColor(THEME["primary"])
        canvas.roundRect(
            panel_margin + 10,
            header_y,
            panel_width - 20,
            header_height,
            8,
            fill=1,
            stroke=0,
        )
        
        canvas.setFillColor(colors.white)
        canvas.setFont("NotoSans-Bold", 11)
        canvas.drawString(panel_margin + 30, header_y + 13, "Stateless as Wind")
    
    # Footer with page number
    canvas.setFont("NotoSans", 8)
    canvas.setFillColor(THEME["muted"])
    canvas.drawCentredString(width / 2, panel_margin + 12, f"Page {doc.page}")
    
    canvas.restoreState()


def create_cover_image(width: float) -> Image:
    """Create the cover image flowable."""
    if not PHOTO_PATH.exists():
        return None
    
    try:
        reader = ImageReader(str(PHOTO_PATH))
        img_width, img_height = reader.getSize()
    except Exception as e:
        print(f"Error loading image: {e}")
        return None
    
    # Scale to fit width while maintaining aspect ratio
    max_width = width * 0.85
    max_height = 360
    scale = min(max_width / img_width, max_height / img_height, 1.0)
    
    image = Image(str(PHOTO_PATH), width=img_width * scale, height=img_height * scale)
    image.hAlign = "CENTER"
    return image


def parse_content():
    """Load and parse the document content."""
    content_file = ROOT / "original_title_content.json"
    with open(content_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def is_section_heading(text: str) -> bool:
    """Determine if text is a section heading."""
    section_keywords = [
        "General information:",
        "Contact:",
        "Logline",
        "Synopsis",
        "Artistic Approach",
        "Visual material",
        "Director's Notes",
        "Producer's Note",
        "Finance Plan",
        "Outlook & Distribution",
        "Biography:",
        "Filmography:",
        "Festivals",
        "Awards",
        "TV Broadcast",
        "Links to Previous movie:",
    ]
    return any(text.strip().startswith(kw) for kw in section_keywords)


def main():
    register_fonts()
    styles = build_styles()
    
    # Load content
    content = parse_content()
    
    # Create document
    doc = BaseDocTemplate(
        str(OUTPUT_PDF),
        pagesize=A4,
        leftMargin=60,
        rightMargin=60,
        topMargin=140,
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
    
    # === COVER PAGE ===
    story.append(Spacer(1, 20))
    
    # Add cover image
    cover_img = create_cover_image(doc.width)
    if cover_img:
        story.append(cover_img)
        story.append(Spacer(1, 20))
    
    # Title
    story.append(Paragraph("Stateless as Wind", styles["Title"]))
    story.append(Paragraph("2015–2025", styles["Subtitle"]))
    story.append(accent_divider(doc.width * 0.6))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Autobiographical Documentary by Samereh Rezaei / Jala Film", styles["Subtitle"]))
    story.append(Spacer(1, 20))
    
    # Process content
    in_cover = True
    current_section = None
    
    for item in content:
        text = item['text'].strip()
        
        if not text:
            continue
        
        # Skip already rendered cover items
        if in_cover and item['idx'] <= 14:
            continue
        
        # Original title in Persian
        if "Original title:" in text:
            in_cover = False
            story.append(Paragraph("Original Title", styles["Label"]))
            persian_text = text.split(":", 1)[1].strip()
            if persian_text:
                story.append(Paragraph(prepare_rtl(persian_text), styles["Persian"]))
            story.append(Spacer(1, 6))
            continue
        
        # Check for section headings
        if is_section_heading(text):
            story.append(Spacer(1, 20))
            heading_text = text.rstrip(":")
            story.append(section_heading(heading_text, doc.width, styles))
            story.append(Spacer(1, 12))
            current_section = heading_text
            continue
        
        # Handle different content types
        if ":" in text and len(text) < 80:
            # Key-value pairs
            parts = text.split(":", 1)
            if len(parts) == 2:
                label, value = parts
                if value.strip():
                    story.append(Paragraph(f"<b>{label.strip()}:</b> {value.strip()}", styles["BodyLeft"]))
                else:
                    story.append(Paragraph(f"<b>{label.strip()}</b>", styles["Label"]))
            else:
                story.append(Paragraph(text, styles["BodyLeft"]))
        elif text.startswith("http"):
            # Links
            story.append(Paragraph(f'<link href="{text}">{text}</link>', styles["Small"]))
        else:
            # Regular body text
            story.append(Paragraph(text, styles["Body"]))
    
    # Build the PDF
    doc.build(story)
    print(f"✓ Created {OUTPUT_PDF.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
