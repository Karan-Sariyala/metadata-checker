import io
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor, black, white, Color
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Frame, BaseDocTemplate, PageTemplate,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Circle, String
from reportlab.graphics import renderPDF
from app.models.schemas import AnalysisReport, Finding

PAGE_W, PAGE_H = A4
MARGIN = 2 * cm
DARK = HexColor("#0f0f0f")
GRAY_BG = HexColor("#f4f4f4")
GRAY_LIGHT = HexColor("#e5e5e5")
GRAY_TEXT = HexColor("#666666")
SEVERITY_COLORS = {
    "Low": HexColor("#3b82f6"),
    "Medium": HexColor("#f59e0b"),
    "High": HexColor("#ef4444"),
}
RISK_COLORS = {
    "Low": HexColor("#22c55e"),
    "Medium": HexColor("#f59e0b"),
    "High": HexColor("#ef4444"),
}


def _severity_bg(sev: str) -> Color:
    c = SEVERITY_COLORS.get(sev)
    if c is None:
        return GRAY_LIGHT
    r, g, b = c.red, c.green, c.blue
    return Color(r, g, b, alpha=0.2)


styles = getSampleStyleSheet()
styles.add(ParagraphStyle("DarkTitle", parent=styles["Normal"], fontSize=10, textColor=white, fontName="Helvetica-Bold"))
styles.add(ParagraphStyle("DocName", parent=styles["Normal"], fontSize=18, textColor=black, fontName="Helvetica-Bold", spaceAfter=4))
styles.add(ParagraphStyle("SmallMeta", parent=styles["Normal"], fontSize=9, textColor=GRAY_TEXT))
styles.add(ParagraphStyle("SummaryText", parent=styles["Normal"], fontSize=10, textColor=black, leading=14))
styles.add(ParagraphStyle("FooterText", parent=styles["Normal"], fontSize=7.5, textColor=GRAY_TEXT, alignment=TA_CENTER))
styles.add(ParagraphStyle("TableHeader", parent=styles["Normal"], fontSize=8.5, textColor=white, fontName="Helvetica-Bold"))
styles.add(ParagraphStyle("TableCell", parent=styles["Normal"], fontSize=8.5, textColor=black))
styles.add(ParagraphStyle("RiskScore", parent=styles["Normal"], fontSize=28, textColor=white, fontName="Helvetica-Bold", alignment=TA_CENTER))
styles.add(ParagraphStyle("RiskLabel", parent=styles["Normal"], fontSize=10, textColor=white, alignment=TA_CENTER, spaceBefore=2))


def _header_table(report: AnalysisReport) -> Table:
    today = date.today().strftime("%B %d, %Y")
    data = [
        [
            Paragraph("METADATA ANALYSIS REPORT", styles["DarkTitle"]),
            Paragraph(today, ParagraphStyle("DateRight", parent=styles["DarkTitle"], alignment=TA_RIGHT, fontSize=8)),
        ]
    ]
    t = Table(data, colWidths=[PAGE_W - 2 * MARGIN - 120, 120])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), DARK),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    return t


def _risk_circle(score: int, level: str) -> Drawing:
    color = RISK_COLORS.get(level, GRAY_TEXT)
    d = Drawing(80, 80)
    d.add(Circle(40, 40, 36, fillColor=color, strokeColor=color, strokeWidth=2))
    d.add(String(40, 38, str(score), textAnchor="middle", fontSize=22, fontName="Helvetica-Bold", fillColor=white))
    return d


def _build_report(report: AnalysisReport) -> list:
    elements = []

    elements.append(_header_table(report))
    elements.append(Spacer(1, 16))

    elements.append(Paragraph(report.document_name, styles["DocName"]))
    elements.append(Paragraph(
        f"{report.file_type} &mdash; {report.extracted_metadata.file_size_bytes:,} bytes",
        styles["SmallMeta"],
    ))
    elements.append(Spacer(1, 14))

    risk_table = Table(
        [[_risk_circle(report.metadata_risk_score, report.metadata_risk_level),
          Paragraph(report.metadata_risk_level, styles["RiskLabel"])]],
        colWidths=[80, 80],
    )
    risk_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    wrapper = Table([[risk_table]], colWidths=[PAGE_W - 2 * MARGIN])
    wrapper.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))
    elements.append(wrapper)
    elements.append(Spacer(1, 14))

    summary_data = [[Paragraph(report.summary, styles["SummaryText"])]]
    summary_table = Table(summary_data, colWidths=[PAGE_W - 2 * MARGIN - 20])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HexColor("#f0f0f0")),
        ("BOX", (0, 0), (-1, -1), 0.5, GRAY_LIGHT),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 14))

    elements.append(Paragraph("Extracted Metadata", styles["Heading6"]))
    elements.append(Spacer(1, 4))
    meta = report.extracted_metadata
    meta_rows = [
        ["Field", "Value"],
        ["File Name", meta.file_name],
        ["File Size", f"{meta.file_size_bytes:,} bytes"],
        ["File Type", meta.file_type],
        ["PDF Version", meta.pdf_version or "\u2014"],
        ["Created Date", meta.created_date or "\u2014"],
        ["Modified Date", meta.modified_date or "\u2014"],
        ["Author", meta.author or "\u2014"],
        ["Creator", meta.creator or "\u2014"],
        ["Producer", meta.producer or "\u2014"],
        ["Title", meta.title or "\u2014"],
        ["Subject", meta.subject or "\u2014"],
        ["Page Count", str(meta.page_count) if meta.page_count is not None else "\u2014"],
        ["Encrypted", str(meta.is_encrypted) if meta.is_encrypted is not None else "\u2014"],
    ]
    meta_table = Table(meta_rows, colWidths=[120, PAGE_W - 2 * MARGIN - 140])
    meta_style = [
        ("BACKGROUND", (0, 0), (-1, 0), DARK),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.5, GRAY_LIGHT),
    ]
    for i in range(1, len(meta_rows)):
        if i % 2 == 0:
            meta_style.append(("BACKGROUND", (0, i), (-1, i), GRAY_BG))
    meta_table.setStyle(TableStyle(meta_style))
    elements.append(meta_table)
    elements.append(Spacer(1, 14))

    elements.append(Paragraph(f"Findings ({len(report.findings)})", styles["Heading6"]))
    elements.append(Spacer(1, 4))
    find_rows = [["Finding", "Severity", "Conf.", "Explanation"]]
    for f in report.findings:
        find_rows.append([
            Paragraph(f.title, styles["TableCell"]),
            Paragraph(f.severity, styles["TableCell"]),
            f"{round(f.confidence * 100)}%",
            Paragraph(f.explanation, styles["TableCell"]),
        ])
    find_table = Table(find_rows, colWidths=[100, 55, 40, PAGE_W - 2 * MARGIN - 215])
    find_style = [
        ("BACKGROUND", (0, 0), (-1, 0), DARK),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("GRID", (0, 0), (-1, -1), 0.5, GRAY_LIGHT),
    ]
    for i in range(1, len(find_rows)):
        sev = report.findings[i - 1].severity
        find_style.append(("BACKGROUND", (1, i), (1, i), _severity_bg(sev)))
    find_table.setStyle(TableStyle(find_style))
    elements.append(find_table)
    elements.append(Spacer(1, 14))

    footer_text = (
        "This report identifies metadata signals only. It does not constitute "
        "proof of document tampering or fraud."
    )
    elements.append(Paragraph(footer_text, styles["FooterText"]))

    return elements


class PDFReportGenerator:

    def generate(self, report: AnalysisReport) -> bytes:
        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=A4,
            leftMargin=MARGIN,
            rightMargin=MARGIN,
            topMargin=10 * mm,
            bottomMargin=10 * mm,
        )
        elements = _build_report(report)
        doc.build(elements)
        return buf.getvalue()


generator = PDFReportGenerator()
