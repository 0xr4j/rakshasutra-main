"""Build the reading copy by appending the transparent Table 5/8 erratum."""

from io import BytesIO
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "paper" / "rakshasutra_double_column_tables_fixed_source.pdf"
OUTPUT = ROOT / "paper" / "rakshasutra_open.pdf"


def erratum_page() -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=22 * mm,
        bottomMargin=20 * mm,
        title="Repository-prepared arithmetic erratum for Rakshasutra",
        author="Repository correction sheet",
    )
    base = getSampleStyleSheet()
    title = ParagraphStyle("ErratumTitle", parent=base["Title"], alignment=TA_LEFT,
                           textColor=colors.HexColor("#12304a"), fontSize=19, leading=23,
                           spaceAfter=8 * mm)
    body = ParagraphStyle("ErratumBody", parent=base["BodyText"], fontSize=10.5,
                          leading=15, spaceAfter=4 * mm)
    small = ParagraphStyle("ErratumSmall", parent=body, fontSize=9, leading=12,
                           textColor=colors.HexColor("#3f4d5a"))
    head = ParagraphStyle("ErratumHead", parent=body, fontName="Helvetica-Bold",
                          textColor=colors.white, fontSize=9)

    story = [
        Paragraph("Arithmetic erratum: LoRaWAN collision-loss entries", title),
        Paragraph("Applies to <i>Rakshasutra (SurakshaNet): A Zero-UI Cognitive-Assistive Wearable and Edge-Filtered BLE–LoRaWAN Architecture for Spatial Disorientation and Crowd Localization in Cellular-Denied Mountain Pilgrimages</i>, supplied 21 October 2026.", body),
        Paragraph("The supplied PDF gives the pure-ALOHA loss relation as P<sub>loss</sub> = 1 - exp(-2G). Recomputing from the displayed Table 5 offered-load values gives the corrected pairs below. The source PDF is preserved unchanged before this addendum in this reading copy.", body),
    ]
    data = [
        [Paragraph("Case (3,000 tags)", head), Paragraph("Displayed G", head),
         Paragraph("Loss in supplied Table 5", head), Paragraph("Recomputed loss", head)],
        ["60 poles, explicit departures", "17.11%", "28.99%", "28.98%"],
        ["60 poles, implicit departures", "11.98%", "21.35%", "21.31%"],
        ["40 LoRa poles + fiber hubs", "7.99%", "14.77%", "14.77%"],
    ]
    table = Table(data, colWidths=[58 * mm, 25 * mm, 42 * mm, 35 * mm], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#12304a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#aab6c2")),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f5f8fb")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.extend([table, Spacer(1, 7 * mm)])
    story.append(Paragraph("Table 8 also carries forward the earlier “15.8% loss (G = 8.6%) at 60 poles” statement. That pair is superseded for the revised 3,000-tag cases: use 28.98% for the explicit-departure case and 21.31% for the implicit-departure case when calculations are based on the displayed Table 5 loads. The 40-pole fiber-offload value remains 14.77% at the displayed precision.", body))
    story.append(Paragraph("Scope: these are formula checks on manuscript-reported offered loads, not measured radio performance or field data. Because the uploaded PDF's editable TeX source was not included, this repository-prepared page is appended transparently rather than silently editing the original pages. For a clean publication master, apply these corrections in the manuscript source and regenerate the tables from unrounded loads.", small))
    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph("Repository-generated correction sheet · source manuscript remains preserved · analytical arithmetic only", ParagraphStyle("Footer", parent=small, alignment=TA_CENTER)))
    doc.build(story)
    return buffer.getvalue()


def main() -> None:
    if not SOURCE.exists():
        raise FileNotFoundError(f"Preserved source PDF not found: {SOURCE}")
    writer = PdfWriter()
    for page in PdfReader(str(SOURCE)).pages:
        writer.add_page(page)
    appendix = PdfReader(BytesIO(erratum_page()))
    writer.add_page(appendix.pages[0])
    writer.add_metadata({
        "/Title": "Rakshasutra (SurakshaNet) — supplied manuscript with repository arithmetic erratum",
        "/Subject": "10-page source manuscript plus transparent Table 5/Table 8 correction sheet",
    })
    with OUTPUT.open("wb") as stream:
        writer.write(stream)
    print(f"Wrote {OUTPUT} ({len(writer.pages)} pages). Source pages were not modified.")


if __name__ == "__main__":
    main()
