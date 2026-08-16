"""Behaviour record management."""

from sqlalchemy import select

from database.connection import get_session
from models.communication import BehaviourRecord


def create_behaviour_record(student_id: str, recorded_by: str, category: str, description: str,
                             disciplinary_action: str = "") -> tuple[bool, str]:
    if category not in ("positive", "negative"):
        return False, "Category must be positive or negative."
    if not description.strip():
        return False, "Description is required."
    db = get_session()
    try:
        db.add(BehaviourRecord(
            student_id=student_id, recorded_by=recorded_by, category=category,
            description=description.strip(), disciplinary_action=disciplinary_action or None,
        ))
        db.commit()
        return True, "Behaviour record saved."
    finally:
        db.close()


def list_behaviour_records(student_id: str) -> list[BehaviourRecord]:
    db = get_session()
    try:
        return list(db.execute(
            select(BehaviourRecord)
            .where(BehaviourRecord.student_id == student_id)
            .order_by(BehaviourRecord.created_at.desc())
        ).scalars().all())
    finally:
        db.close()


def resolve_behaviour_record(record_id: str, notify_parent: bool = False) -> tuple[bool, str]:
    db = get_session()
    try:
        record = db.get(BehaviourRecord, record_id)
        if record is None:
            return False, "Record not found."
        record.action_status = "resolved"
        if notify_parent:
            record.parent_notified = True
        db.commit()
        return True, "Behaviour record resolved."
    finally:
        db.close()


def behaviour_summary(student_id: str) -> dict:
    records = list_behaviour_records(student_id)
    positive = sum(1 for r in records if r.category == "positive")
    negative = sum(1 for r in records if r.category == "negative")
    return {"total": len(records), "positive": positive, "negative": negative}
