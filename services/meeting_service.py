"""Parent-teacher meeting requests and PTA meetings."""

from sqlalchemy import select

from database.connection import get_session
from models.communication import Meeting, PTAMeeting


def request_meeting(requested_by: str, teacher_id: str | None, student_id: str | None,
                     reason: str, requested_time=None) -> tuple[bool, str]:
    db = get_session()
    try:
        db.add(Meeting(
            requested_by=requested_by, teacher_id=teacher_id, student_id=student_id,
            reason=reason, requested_time=requested_time, status="pending",
        ))
        db.commit()
        return True, "Meeting request submitted."
    finally:
        db.close()


def list_meetings_for_user(user_id: str) -> list[Meeting]:
    db = get_session()
    try:
        return list(db.execute(
            select(Meeting).where(Meeting.requested_by == user_id).order_by(Meeting.created_at.desc())
        ).scalars().all())
    finally:
        db.close()


def list_meetings_for_teacher(teacher_profile_id: str) -> list[Meeting]:
    db = get_session()
    try:
        return list(db.execute(
            select(Meeting).where(Meeting.teacher_id == teacher_profile_id).order_by(Meeting.created_at.desc())
        ).scalars().all())
    finally:
        db.close()


def update_meeting_status(meeting_id: str, status: str) -> tuple[bool, str]:
    db = get_session()
    try:
        meeting = db.get(Meeting, meeting_id)
        if meeting is None:
            return False, "Meeting not found."
        meeting.status = status
        db.commit()
        return True, "Meeting updated."
    finally:
        db.close()


def create_pta_meeting(created_by: str, title: str, scheduled_at=None) -> tuple[bool, str]:
    if not title.strip():
        return False, "Title is required."
    db = get_session()
    try:
        db.add(PTAMeeting(created_by=created_by, title=title.strip(), scheduled_at=scheduled_at))
        db.commit()
        return True, "PTA meeting created."
    finally:
        db.close()


def list_pta_meetings() -> list[PTAMeeting]:
    db = get_session()
    try:
        return list(db.execute(select(PTAMeeting).order_by(PTAMeeting.scheduled_at.desc())).scalars().all())
    finally:
        db.close()


def record_pta_minutes(meeting_id: str, minutes: str) -> tuple[bool, str]:
    db = get_session()
    try:
        meeting = db.get(PTAMeeting, meeting_id)
        if meeting is None:
            return False, "Meeting not found."
        meeting.minutes = minutes
        db.commit()
        return True, "Minutes recorded."
    finally:
        db.close()
