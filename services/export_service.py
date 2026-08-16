"""
Reporting and exports.

Generates CSV/Excel bytes directly from the database for authorized users.
Every export is recorded in ExportHistory for traceability.
"""

import io

import pandas as pd
from sqlalchemy import select

from database.connection import get_session
from models.settings import ExportHistory
from services import people_service, attendance_service, results_service


def _record_export(exported_by: str, export_type: str, module: str, file_name: str):
    db = get_session()
    try:
        db.add(ExportHistory(exported_by=exported_by, export_type=export_type, module=module, file_name=file_name))
        db.commit()
    finally:
        db.close()


def export_students_csv(exported_by: str) -> bytes:
    students = people_service.list_students()
    df = pd.DataFrame(students)
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    _record_export(exported_by, "csv", "students", "students_export.csv")
    return buffer.getvalue().encode("utf-8")


def export_students_excel(exported_by: str) -> bytes:
    students = people_service.list_students()
    df = pd.DataFrame(students)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Students")
    _record_export(exported_by, "excel", "students", "students_export.xlsx")
    buffer.seek(0)
    return buffer.getvalue()


def export_class_results_csv(exported_by: str, class_id: str, subject_id: str, term_id: str) -> bytes:
    rows = results_service.get_class_results(class_id, subject_id, term_id)
    df = pd.DataFrame(rows)
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    _record_export(exported_by, "csv", "results", "results_export.csv")
    return buffer.getvalue().encode("utf-8")


def list_export_history(limit: int = 50) -> list[ExportHistory]:
    db = get_session()
    try:
        return list(db.execute(
            select(ExportHistory).order_by(ExportHistory.created_at.desc()).limit(limit)
        ).scalars().all())
    finally:
        db.close()
