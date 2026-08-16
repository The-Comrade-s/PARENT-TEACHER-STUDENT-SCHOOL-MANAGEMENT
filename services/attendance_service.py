"""Attendance business logic."""

from datetime import date as date_type

from sqlalchemy import select, func

from database.connection import get_session
from models.academic import AttendanceRecord
from models.people import StudentProfile


def get_class_attendance_for_date(class_id: str, on_date: date_type) -> dict[str, AttendanceRecord]:
    db = get_session()
    try:
        records = db.execute(
            select(AttendanceRecord).where(
                AttendanceRecord.class_id == class_id, AttendanceRecord.date == on_date
            )
        ).scalars().all()
        return {r.student_id: r for r in records}
    finally:
        db.close()


def get_class_roster(class_id: str) -> list[StudentProfile]:
    db = get_session()
    try:
        return list(db.execute(
            select(StudentProfile).where(
                StudentProfile.current_class_id == class_id, StudentProfile.student_status == "active"
            )
        ).scalars().all())
    finally:
        db.close()


def save_attendance(class_id: str, on_date: date_type, statuses: dict[str, str], marked_by: str) -> tuple[bool, str]:
    """statuses: {student_id: 'present'|'absent'|'late'|'excused'}"""
    db = get_session()
    try:
        existing = db.execute(
            select(AttendanceRecord).where(
                AttendanceRecord.class_id == class_id, AttendanceRecord.date == on_date
            )
        ).scalars().all()
        existing_by_student = {r.student_id: r for r in existing}

        if existing and any(r.is_locked for r in existing):
            return False, "Attendance for this date is locked and cannot be modified."

        for student_id, status in statuses.items():
            record = existing_by_student.get(student_id)
            if record is None:
                db.add(AttendanceRecord(
                    student_id=student_id, class_id=class_id, date=on_date,
                    status=status, marked_by=marked_by,
                ))
            else:
                record.status = status
                record.marked_by = marked_by
        db.commit()
        return True, "Attendance saved."
    finally:
        db.close()


def lock_attendance(class_id: str, on_date: date_type) -> tuple[bool, str]:
    db = get_session()
    try:
        records = db.execute(
            select(AttendanceRecord).where(
                AttendanceRecord.class_id == class_id, AttendanceRecord.date == on_date
            )
        ).scalars().all()
        if not records:
            return False, "No attendance recorded for this date yet."
        for r in records:
            r.is_locked = True
        db.commit()
        return True, "Attendance locked."
    finally:
        db.close()


def reopen_attendance(class_id: str, on_date: date_type) -> tuple[bool, str]:
    db = get_session()
    try:
        records = db.execute(
            select(AttendanceRecord).where(
                AttendanceRecord.class_id == class_id, AttendanceRecord.date == on_date
            )
        ).scalars().all()
        for r in records:
            r.is_locked = False
        db.commit()
        return True, "Attendance reopened."
    finally:
        db.close()


def class_attendance_summary(class_id: str) -> dict:
    db = get_session()
    try:
        total = db.execute(
            select(func.count(AttendanceRecord.id)).where(AttendanceRecord.class_id == class_id)
        ).scalar_one()
        present = db.execute(
            select(func.count(AttendanceRecord.id)).where(
                AttendanceRecord.class_id == class_id, AttendanceRecord.status == "present"
            )
        ).scalar_one()
        rate = round((present / total) * 100, 1) if total else 0.0
        return {"total_records": total, "present_records": present, "attendance_rate": rate}
    finally:
        db.close()


def student_attendance_summary(student_id: str) -> dict:
    db = get_session()
    try:
        total = db.execute(
            select(func.count(AttendanceRecord.id)).where(AttendanceRecord.student_id == student_id)
        ).scalar_one()
        present = db.execute(
            select(func.count(AttendanceRecord.id)).where(
                AttendanceRecord.student_id == student_id, AttendanceRecord.status == "present"
            )
        ).scalar_one()
        rate = round((present / total) * 100, 1) if total else 0.0
        return {"total_records": total, "present_records": present, "attendance_rate": rate}
    finally:
        db.close()
