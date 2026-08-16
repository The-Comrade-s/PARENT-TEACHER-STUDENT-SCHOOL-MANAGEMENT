"""Report card PDF generation, built directly in Python with reportlab."""

import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

from config.settings import settings
from services import school_service, results_service, attendance_service


def _current_term_id() -> str | None:
    term = school_service.get_current_term()
    return term.id if term else None


def generate_report_card_pdf(student_admission_number: str, student_name: str, class_name: str,
                              student_id: str, term_name: str, session_name: str) -> bytes:
    results = results_service.get_student_results(student_id, term_id=_current_term_id(), published_only=True)
    attendance = attendance_service.student_attendance_summary(student_id)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1.5 * cm, bottomMargin=1.5 * cm)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "PTMSTitle", parent=styles["Heading1"], textColor=colors.HexColor(settings.color_primary),
        alignment=1,
    )
    normal_style = styles["Normal"]

    elements = [
        Paragraph("Student Report Card", title_style),
        Spacer(1, 0.3 * cm),
        Paragraph(f"Session: {session_name} &nbsp;&nbsp; Term: {term_name}", normal_style),
        Spacer(1, 0.5 * cm),
        Paragraph(f"Student: {student_name}", normal_style),
        Paragraph(f"Admission Number: {student_admission_number}", normal_style),
        Paragraph(f"Class: {class_name}", normal_style),
        Spacer(1, 0.5 * cm),
    ]

    table_data = [["Subject", "CA Score", "Exam Score", "Total", "Grade", "Remark"]]
    for r in results:
        table_data.append([
            r["subject_name"], str(r["ca_score"]), str(r["exam_score"]),
            str(r["total_score"]), r["grade"] or "", r["remark"] or "",
        ])
    if len(table_data) == 1:
        table_data.append(["No published results yet", "", "", "", "", ""])

    result_table = Table(table_data, colWidths=[4.5 * cm, 2.2 * cm, 2.2 * cm, 2 * cm, 2 * cm, 3.5 * cm])
    result_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(settings.color_primary)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F0F0EA")]),
    ]))
    elements.append(result_table)
    elements.append(Spacer(1, 0.6 * cm))

    elements.append(Paragraph(
        f"Attendance Summary: {attendance['present_records']} of {attendance['total_records']} "
        f"days present ({attendance['attendance_rate']} percent)", normal_style
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
