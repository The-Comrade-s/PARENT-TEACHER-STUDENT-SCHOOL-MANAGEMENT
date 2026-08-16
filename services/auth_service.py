"""
Authentication and registration business logic.

All database writes for identity and role assignment go through this
service so there is exactly one place that owns those rules.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from auth.security import hash_password, verify_password, password_meets_policy
from config.settings import settings
from database.connection import get_session
from models.people import TeacherProfile, ParentProfile, StudentProfile
from models.school import SchoolClass
from models.user import User, Role, AuditLog
from permissions.rbac import ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN, ROLE_TEACHER, ROLE_PARENT, ROLE_STUDENT

SYSTEM_ROLES = {
    ROLE_SUPER_ADMIN: "Super Administrator",
    ROLE_SCHOOL_ADMIN: "School Administrator",
    ROLE_TEACHER: "Teacher",
    ROLE_PARENT: "Parent",
    ROLE_STUDENT: "Student",
}


def log_action(user_email: str | None, action: str, module: str, details: str = "", user_id: str | None = None):
    db = get_session()
    try:
        db.add(AuditLog(user_id=user_id, user_email=user_email, action=action, module=module, details=details))
        db.commit()
    finally:
        db.close()


def seed_roles_and_admin():
    """
    Idempotent seed: creates the five system roles and a default super admin
    if none exists yet. Safe to call on every app startup.
    """
    db = get_session()
    try:
        for role_name, display_name in SYSTEM_ROLES.items():
            existing = db.execute(select(Role).where(Role.name == role_name)).scalar_one_or_none()
            if existing is None:
                db.add(Role(name=role_name, display_name=display_name, is_system_role=True))
        db.commit()

        admin_exists = db.execute(
            select(User).join(User.roles).where(Role.name == ROLE_SUPER_ADMIN)
        ).first()
        if admin_exists is None:
            super_admin_role = db.execute(select(Role).where(Role.name == ROLE_SUPER_ADMIN)).scalar_one()
            admin_user = User(
                first_name="System",
                last_name="Administrator",
                email=settings.default_admin_email,
                hashed_password=hash_password(settings.default_admin_password),
                status="active",
            )
            admin_user.roles.append(super_admin_role)
            db.add(admin_user)
            db.commit()
    finally:
        db.close()


def authenticate(email: str, password: str) -> tuple[User | None, str]:
    """Returns (user_or_None, message). Handles lockout and failed-attempt tracking."""
    db = get_session()
    try:
        user = db.execute(select(User).where(User.email == email.strip().lower())).scalar_one_or_none()
        if user is None:
            return None, "Invalid email or password."

        now = datetime.now(timezone.utc)
        if user.locked_until and user.locked_until > now:
            minutes_left = int((user.locked_until - now).total_seconds() // 60) + 1
            return None, f"Account locked. Try again in {minutes_left} minute(s)."

        if user.status == "pending":
            return None, "Your account is pending approval."
        if user.status != "active":
            return None, "Your account is not active. Contact an administrator."

        if not verify_password(password, user.hashed_password):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= settings.max_failed_login_attempts:
                user.locked_until = now + timedelta(minutes=settings.account_lock_minutes)
                user.failed_login_attempts = 0
            db.commit()
            log_action(email, "login_failed", "auth")
            return None, "Invalid email or password."

        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = now
        db.commit()
        db.refresh(user)
        user_id = user.id
        log_action(email, "login_success", "auth", user_id=user_id)

        # Return a fresh, session-attached copy; the caller (the login page)
        # is responsible for starting the UI session via auth.session.login().
        stmt = select(User).where(User.id == user_id)
        fresh = db.execute(stmt).scalar_one()
        db.expunge(fresh)
        return fresh, "success"
    finally:
        db.close()


def email_in_use(email: str) -> bool:
    db = get_session()
    try:
        return db.execute(select(User).where(User.email == email.strip().lower())).first() is not None
    finally:
        db.close()


def register_parent(first_name: str, last_name: str, email: str, password: str, phone: str = "") -> tuple[bool, str]:
    valid, msg = password_meets_policy(password, settings.min_password_length)
    if not valid:
        return False, msg
    if email_in_use(email):
        return False, "An account with this email already exists."

    db = get_session()
    try:
        role = db.execute(select(Role).where(Role.name == ROLE_PARENT)).scalar_one()
        user = User(
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            email=email.strip().lower(),
            phone_number=phone.strip() or None,
            hashed_password=hash_password(password),
            status="active",
        )
        user.roles.append(role)
        db.add(user)
        db.flush()
        db.add(ParentProfile(user_id=user.id))
        db.commit()
        log_action(email, "register", "auth", "role=parent")
        return True, "Registration successful. You can now log in."
    finally:
        db.close()


def register_teacher(
    first_name: str, last_name: str, email: str, password: str, class_id: str | None, phone: str = ""
) -> tuple[bool, str]:
    """Teacher accounts are created in 'pending' status and require admin approval."""
    valid, msg = password_meets_policy(password, settings.min_password_length)
    if not valid:
        return False, msg
    if email_in_use(email):
        return False, "An account with this email already exists."

    db = get_session()
    try:
        role = db.execute(select(Role).where(Role.name == ROLE_TEACHER)).scalar_one()
        user = User(
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            email=email.strip().lower(),
            phone_number=phone.strip() or None,
            hashed_password=hash_password(password),
            status="pending",
        )
        user.roles.append(role)
        db.add(user)
        db.flush()
        db.add(TeacherProfile(user_id=user.id, approval_status="pending"))
        # Requested class is recorded via a pending note in employment status;
        # actual assignment happens atomically at approval time (see teacher_service).
        db.commit()

        if class_id:
            from services import school_service

            school_service.record_requested_class(user.id, class_id)

        log_action(email, "register", "auth", "role=teacher, status=pending")
        return True, "Registration successful. Your account is pending administrator approval."
    finally:
        db.close()


def get_active_classes_for_registration() -> list[dict]:
    """Loads active classes directly from the database for the registration form's class selector."""
    db = get_session()
    try:
        classes = db.execute(
            select(SchoolClass).where(SchoolClass.is_active == True)  # noqa: E712
        ).scalars().all()
        return [{"id": c.id, "label": f"{c.name}"} for c in classes]
    finally:
        db.close()
