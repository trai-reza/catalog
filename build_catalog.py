import os
from pathlib import Path

from docx import Document
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, inch
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def escape(text: str) -> str:
    """Escape characters that are special in ReportLab's para markup."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br/>")
    )


def format_label_value(text: str) -> str:
    if ":" in text:
        label, value = text.split(":", 1)
        label = label.strip()
        value = value.lstrip()
        return f"<b>{escape(label)}:</b> {escape(value)}"
    return escape(text)


def build_catalogue():
    # Paths and data
    root = Path(".")
    docx_path = root / "main-content.docx"
    image_dir = root / "assets" / "photos"

    if not docx_path.exists():
        raise FileNotFoundError("main-content.docx not found.")
    if not image_dir.exists():
        raise FileNotFoundError("Expected images in assets/photos directory.")

    captions = {
        "photo01.png": "Stateless as wind\nAutobiographical Documentary by Samereh Rezaei  2015_2025",
        "photo02.jpeg": "Iran, Tehran, trying to stay in my hometown, last-ditch pleas to convince the Islamic Republic of Iran Police",
        "photo03.png": "A poetic journey through exile,   womanhood,   and the wind of belonging.",
        "photo04.jpeg": "“Yasna and Delsa” — my brother’s little girls, a third generation still foreign to the land they call home.\nUnaware of what awaits them, they dance — free, bright, and untouched by destiny.",
        "photo05.jpeg": "My mother — a woman who was separated from her home during the Soviet war forty years ago.\nAfter years of struggle, she now tries to preserve what is left of it… but what truly remains of home?",
        "photo06.jpeg": "Afghanistan —  the only corner of the world that was truly ours.  Now I stand helpless, watching it crumble, moment by moment…",
        "photo09.png": "The children who become victims of exile — they grow up amid the silence of broken goodbyes, learning too soon what it means for a family to fall apart.",
        "photo10.png": "Women from different generations, gathered in a single frame — each a victim of exile.  Mother, who came to Iran forty years ago. Pari, who grew up on its soil.  Samereh, the second generation, born here.  Yesna and Delsa, the third — children who have never known another land.\nAnd yet, they all carry the same mark of identity: foreign nationals.",
        "photo12.png": "Lost and disoriented, I dance. I take refuge in the inner world, searching for myself.",
        # photo13 has no caption provided; we'll add a short descriptor for the biography section.
        "photo13.jpeg": "Samereh Rezaei during the production journey of “Stateless as Wind”.",
    }

    # Read main content paragraphs
    document = Document(docx_path)
    paragraphs = [p.text.strip() for p in document.paragraphs if p.text.strip()]

    # Locate key section indices
    index = {text: paragraphs.index(text) for text in [
        "General information:",
        "Contact:",
        "Logline",
        "Synopsis",
        "Artistic Approach",
        "Director's Notes",
        "Producer’s Note",
        "Finance Plan",
        "Outlook & Distribution",
        "Biography:",
        "Filmography:",
        "Links to Previous movie:",
    ]}

    output_pdf = root / "stateless-as-wind-cataloge.pdf"
    doc = SimpleDocTemplate(
        str(output_pdf),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2.2 * cm,
        bottomMargin=2.0 * cm,
    )

    page_width = doc.width

    # Styles
    base_styles = getSampleStyleSheet()
    primary = colors.HexColor("#142840")
    accent = colors.HexColor("#C0594D")
    muted = colors.HexColor("#585A5C")

    title_style = ParagraphStyle(
        "Title",
        parent=base_styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=28,
        leading=32,
        alignment=TA_CENTER,
        textColor=primary,
        spaceAfter=12,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=base_styles["Normal"],
        fontName="Helvetica",
        fontSize=14,
        leading=18,
        alignment=TA_CENTER,
        textColor=accent,
        spaceAfter=18,
    )
    meta_style = ParagraphStyle(
        "Meta",
        parent=base_styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#1f1f1f"),
        spaceAfter=8,
    )
    info_style = ParagraphStyle(
        "Info",
        parent=meta_style,
        leftIndent=10,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=base_styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=16,
        textColor=colors.HexColor("#111111"),
        spaceAfter=12,
    )
    section_title_style = ParagraphStyle(
        "SectionTitle",
        parent=base_styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=colors.white,
    )
    subheader_style = ParagraphStyle(
        "SubHeader",
        parent=body_style,
        fontName="Helvetica-Bold",
        textColor=accent,
        spaceBefore=12,
        spaceAfter=6,
    )
    caption_style = ParagraphStyle(
        "Caption",
        parent=base_styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=9,
        leading=12,
        alignment=TA_CENTER,
        textColor=muted,
        spaceAfter=16,
    )

    def section_header(text: str) -> Table:
        header_para = Paragraph(escape(text), section_title_style)
        table = Table([[header_para]], colWidths=[page_width])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), primary),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        return table

    def image_with_caption(filename: str, caption: str | None, add_top_space: bool = True):
        img_path = image_dir / filename
        if not img_path.exists():
            raise FileNotFoundError(f"Image {filename} not found in assets/photos.")
        img = Image(str(img_path))
        img.drawWidth = page_width
        img.drawHeight = img.imageHeight * (img.drawWidth / img.imageWidth)
        max_height = 5.5 * inch
        if img.drawHeight > max_height:
            scale = max_height / img.drawHeight
            img.drawWidth *= scale
            img.drawHeight = max_height

        elements = []
        if add_top_space:
            elements.append(Spacer(1, 14))
        elements.append(img)
        if caption:
            elements.append(Spacer(1, 6))
            elements.append(Paragraph(escape(caption), caption_style))
        elements.append(Spacer(1, 16))
        return elements

    story: list = []

    # Cover image and caption (consumes first two lines of content)
    story.extend(image_with_caption("photo01.png", captions["photo01.png"], add_top_space=False))

    # Initial metadata (Original title through credits)
    for idx in range(2, index["General information:"]):
        text = paragraphs[idx]
        if text.endswith(":"):
            story.append(Paragraph(f"<b>{escape(text)}</b>", meta_style))
        else:
            story.append(Paragraph(escape(text), meta_style))

    story.append(Spacer(1, 12))

    # General Information section
    story.append(section_header(paragraphs[index["General information:"]]))
    story.append(Spacer(1, 6))
    for idx in range(index["General information:"] + 1, index["Contact:"]):
        story.append(Paragraph(format_label_value(paragraphs[idx]), info_style))

    # Contact section
    story.append(Spacer(1, 10))
    story.append(section_header(paragraphs[index["Contact:"]]))
    story.append(Spacer(1, 6))
    for idx in range(index["Contact:"] + 1, index["Logline"]):
        story.append(Paragraph(escape(paragraphs[idx]), body_style))

    story.extend(image_with_caption("photo02.jpeg", captions["photo02.jpeg"]))

    # Logline
    story.append(section_header(paragraphs[index["Logline"]]))
    story.append(Spacer(1, 6))
    story.append(Paragraph(escape(paragraphs[index["Logline"] + 1]), body_style))
    story.extend(image_with_caption("photo03.png", captions["photo03.png"]))

    # Synopsis
    story.append(section_header(paragraphs[index["Synopsis"]]))
    story.append(Spacer(1, 6))
    synopsis_end = index["Artistic Approach"]
    for idx in range(index["Synopsis"] + 1, synopsis_end):
        story.append(Paragraph(escape(paragraphs[idx]), body_style))
        if idx == index["Synopsis"] + 1:
            story.extend(image_with_caption("photo04.jpeg", captions["photo04.jpeg"]))
        elif idx == index["Synopsis"] + 2:
            story.extend(image_with_caption("photo05.jpeg", captions["photo05.jpeg"]))
        elif idx == index["Synopsis"] + 3:
            story.extend(image_with_caption("photo06.jpeg", captions["photo06.jpeg"]))
        elif idx == index["Synopsis"] + 5:
            story.extend(image_with_caption("photo09.png", captions["photo09.png"]))

    # Artistic Approach
    story.append(section_header(paragraphs[index["Artistic Approach"]]))
    story.append(Spacer(1, 6))
    for offset, idx in enumerate(range(index["Artistic Approach"] + 1, index["Director's Notes"])):
        story.append(Paragraph(escape(paragraphs[idx]), body_style))
        if offset == 0:
            story.extend(image_with_caption("photo10.png", captions["photo10.png"]))
        elif offset == 2:
            story.extend(image_with_caption("photo12.png", captions["photo12.png"]))

    # Director's Notes
    story.append(section_header(paragraphs[index["Director's Notes"]]))
    story.append(Spacer(1, 6))
    for idx in range(index["Director's Notes"] + 1, index["Producer’s Note"]):
        story.append(Paragraph(escape(paragraphs[idx]), body_style))

    # Producer's Note
    story.append(section_header(paragraphs[index["Producer’s Note"]]))
    story.append(Spacer(1, 6))
    for idx in range(index["Producer’s Note"] + 1, index["Finance Plan"]):
        story.append(Paragraph(escape(paragraphs[idx]), body_style))

    # Finance Plan
    story.append(section_header(paragraphs[index["Finance Plan"]]))
    story.append(Spacer(1, 6))
    for idx in range(index["Finance Plan"] + 1, index["Outlook & Distribution"]):
        story.append(Paragraph(escape(paragraphs[idx]), body_style))

    # Outlook & Distribution
    story.append(section_header(paragraphs[index["Outlook & Distribution"]]))
    story.append(Spacer(1, 6))
    for idx in range(index["Outlook & Distribution"] + 1, index["Biography:"]):
        story.append(Paragraph(escape(paragraphs[idx]), body_style))

    # Biography with portrait image
    story.append(section_header(paragraphs[index["Biography:"]]))
    story.append(Spacer(1, 6))
    story.extend(image_with_caption("photo13.jpeg", captions["photo13.jpeg"]))
    for idx in range(index["Biography:"] + 1, index["Filmography:"]):
        story.append(Paragraph(escape(paragraphs[idx]), body_style))

    # Filmography
    story.append(section_header(paragraphs[index["Filmography:"]]))
    story.append(Spacer(1, 6))
    filmography_end = index["Links to Previous movie:"]
    for idx in range(index["Filmography:"] + 1, filmography_end):
        text = paragraphs[idx]
        if text in {"Writer and Director", "Festivals", "Awards", "TV Broadcast"}:
            story.append(Paragraph(escape(text), subheader_style))
        else:
            story.append(Paragraph(escape(text), body_style))

    # Links
    story.append(section_header(paragraphs[index["Links to Previous movie:"]]))
    story.append(Spacer(1, 6))
    for idx in range(index["Links to Previous movie:"] + 1, len(paragraphs)):
        text = paragraphs[idx]
        if text.endswith(":"):
            story.append(Paragraph(escape(text), subheader_style))
        else:
            if text.startswith("http"):
                story.append(
                    Paragraph(
                        f'<link href="{text}">{escape(text)}</link>',
                        body_style,
                    )
                )
            else:
                story.append(Paragraph(escape(text), body_style))

    muted_number_color = colors.HexColor("#8A8C8E")

    def add_page_number(canvas, _doc):
        page_num = canvas.getPageNumber()
        if page_num > 1:
            canvas.setFont("Helvetica", 9)
            canvas.setFillColor(muted_number_color)
            canvas.drawRightString(
                _doc.pagesize[0] - _doc.rightMargin,
                _doc.bottomMargin * 0.6,
                str(page_num),
            )

    doc.build(
        story,
        onFirstPage=add_page_number,
        onLaterPages=add_page_number,
    )

    print(f"Catalogue saved to {output_pdf}")


if __name__ == "__main__":
    build_catalogue()
