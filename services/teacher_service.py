"""
Teacher approval and class-teacher assignment.

This module is the single source of truth for the class-teacher relationship.
SchoolClass.class_teacher_id is the only field that answers "who teaches this
class" -- nothing else in the codebase should set or infer that fact.

Every assignment operation here:
1. Resolves the teacher's profile ID (not the user ID) explicitly.
2. Clears any previous class this teacher was class-teacher of.
3. Clears any previous teacher the target class had.
4. Writes the new relationship on both sides in one transaction.
5. Commits once, so a caller re-reading immediately after sees the final state
   (no stale UI from a partial write).
"""

from sqlalchemy import select

from database.connection import get_session
from models.people import TeacherProfile
from models.school import SchoolClass
from models.user import User


def list_pending_teachers() -> list[dict]:
    db = get_session()
    try:
        rows = db.execute(
            select(TeacherProfile, User)
            .join(User, TeacherProfile.user_id == User.id)
            .where(TeacherProfile.approval_status == "pending")
        ).all()
        result = []
        for profile, user in rows:
            requested_class = None
            if profile.requested_class_id:
                requested_class = db.get(SchoolClass, profile.requested_class_id)
            result.append({
                "teacher_profile_id": profile.id,
                "user_id": user.id,
                "name": user.full_name,
                "email": user.email,
                "requested_class_name": requested_class.name if requested_class else None,
                "requested_class_id": profile.requested_class_id,
            })
        return result
    finally:
        db.close()


def approve_teacher(teacher_profile_id: str, approved_by_user_id: str, assign_requested_class: bool = True) -> tuple[bool, str]:
    db = get_session()
    try:
        profile = db.get(TeacherProfile, teacher_profile_id)
        if profile is None:
            return False, "Teacher profile not found."

        user = db.get(User, profile.user_id)
        if user is None:
            return False, "Linked user account not found."

        profile.approval_status = "approved"
        profile.approved_by = approved_by_user_id
        user.status = "active"

        if assign_requested_class and profile.requested_class_id:
            ok, message = _assign_class_teacher_locked(db, teacher_profile_id, profile.requested_class_id)
            if not ok:
                db.commit()  # still keep the approval even if the class assignment step failed
                return True, f"Teacher approved, but class assignment failed: {message}"

        db.commit()

        from services.auth_service import log_action

        log_action(user.email, "teacher.approve", "people", user_id=approved_by_user_id)
        return True, "Teacher approved successfully."
    finally:
        db.close()


def reject_teacher(teacher_profile_id: str, rejected_by_user_id: str) -> tuple[bool, str]:
    db = get_session()
    try:
        profile = db.get(TeacherProfile, teacher_profile_id)
        if profile is None:
            return False, "Teacher profile not found."
        user = db.get(User, profile.user_id)

        profile.approval_status = "rejected"
        if user:
            user.status = "suspended"
        db.commit()

        from services.auth_service import log_action

        log_action(user.email if user else None, "teacher.reject", "people", user_id=rejected_by_user_id)
        return True, "Teacher registration rejected."
    finally:
        db.close()


def _assign_class_teacher_locked(db, teacher_profile_id: str, class_id: str) -> tuple[bool, str]:
    """Internal: performs the assignment using an already-open session (no separate commit)."""
    target_class = db.get(SchoolClass, class_id)
    if target_class is None:
        return False, "Class not found."

    teacher_profile = db.get(TeacherProfile, teacher_profile_id)
    if teacher_profile is None:
        return False, "Teacher profile not found."

    # Step 1: clear this teacher off any class they were previously class-teacher of.
    previous_classes = db.execute(
        select(SchoolClass).where(SchoolClass.class_teacher_id == teacher_profile_id)
    ).scalars().all()
    for c in previous_classes:
        if c.id != class_id:
            c.class_teacher_id = None

    # Step 2: clear the target class's previous class-teacher, if different.
    target_class.class_teacher_id = teacher_profile_id

    return True, "Assigned."


def assign_class_teacher(teacher_profile_id: str, class_id: str, actor_user_id: str | None = None) -> tuple[bool, str]:
    """
    Public entry point for (re)assigning a class teacher, used from the school-setup UI
    independent of the approval workflow. Handles reassignment correctly: assigning a
    class to a new teacher automatically removes it from whoever had it before.
    """
    db = get_session()
    try:
        ok, message = _assign_class_teacher_locked(db, teacher_profile_id, class_id)
        if ok:
            db.commit()
            from services.auth_service import log_action

            log_action(None, "class.assign_teacher", "school_setup", user_id=actor_user_id)
        return ok, message
    finally:
        db.close()


def remove_class_teacher(class_id: str, actor_user_id: str | None = None) -> tuple[bool, str]:
    db = get_session()
    try:
        target_class = db.get(SchoolClass, class_id)
        if target_class is None:
            return False, "Class not found."
        target_class.class_teacher_id = None
        db.commit()
        from services.auth_service import log_action

        log_action(None, "class.remove_teacher", "school_setup", user_id=actor_user_id)
        return True, "Class teacher removed."
    finally:
        db.close()
