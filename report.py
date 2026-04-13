from __future__ import annotations

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def _safe_text(value: str) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br/>")
    )


def generate_pdf(report_data, file_path: str = "report.pdf") -> str:
    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()
    body = ParagraphStyle(
        "ReportBody",
        parent=styles["BodyText"],
        fontSize=10,
        leading=14,
        spaceAfter=8,
    )
    section = ParagraphStyle(
        "SectionTitle",
        parent=styles["Heading2"],
        textColor=colors.HexColor("#1f4e79"),
        spaceBefore=10,
        spaceAfter=6,
    )

    content = [
        Paragraph("AI Data Analysis Report", styles["Title"]),
        Spacer(1, 0.15 * inch),
    ]

    sections = [
        ("Overview", report_data.get("overview", [])),
        ("Cleaning Summary", report_data.get("cleaning_notes", [])),
        ("Key Insights", report_data.get("insights", [])),
        ("Correlations", report_data.get("correlations", [])),
    ]

    for title, items in sections:
        content.append(Paragraph(title, section))
        for item in items:
            content.append(Paragraph(_safe_text(f"- {item}"), body))

    visuals = report_data.get("visuals", [])
    if visuals:
        content.append(Paragraph("Recommended Visuals", section))
        for visual in visuals:
            content.append(
                Paragraph(
                    _safe_text(
                        f"- {visual.get('title', 'Chart')}: {visual.get('kind', 'visual').title()} chart"
                    ),
                    body,
                )
            )

    ai_summary = report_data.get("ai_summary")
    if ai_summary:
        content.append(Paragraph("AI Enhancement", section))
        content.append(Paragraph(_safe_text(ai_summary), body))

    content.append(Paragraph("Run Status", section))
    content.append(Paragraph(_safe_text(report_data.get("ai_status", "Completed.")), body))

    doc.build(content)
    return file_path
