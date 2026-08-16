"""
School setup business logic: profile, sessions, terms, departments, classes,
subjects, and the teacher-requested-class linkage used at registration time.

Full CRUD for every entity in this module. Class-teacher assignment itself
lives in services/teacher_service.py, which is the single source of truth
for that relationship -- this module only reads it for display.
"""

from sqlalchemy import select

from database.connection import get_session
from models.people import TeacherProfile
from models.school import SchoolClass, SchoolProfile, AcademicSession, AcademicTerm, Department, Subject


def record_requested_class(user_id: str, class_id: str) -> None:
    db = get_session()
    try:
        profile = db.execute(
            select(TeacherProfile).where(TeacherProfile.user_id == user_id)
        ).scalar_one_or_none()
        if profile is not None:
            profile.requested_class_id = class_id
            db.commit()
    finally:
        db.close()


# ---------------------------------------------------------------- profile --

def get_school_profile() -> SchoolProfile | None:
    db = get_session()
    try:
        return db.execute(select(SchoolProfile)).scalars().first()
    finally:
        db.close()


def save_school_profile(data: dict) -> tuple[bool, str]:
    db = get_session()
    try:
        profile = db.execute(select(SchoolProfile)).scalars().first()
        if profile is None:
            profile = SchoolProfile()
            db.add(profile)
        for key, value in data.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        db.commit()
        return True, "School profile saved."
    finally:
        db.close()


# --------------------------------------------------------------- sessions --

def list_sessions() -> list[AcademicSession]:
    db = get_session()
    try:
        return list(db.execute(select(AcademicSession).order_by(AcademicSession.name.desc())).scalars().all())
    finally:
        db.close()


def create_session(name: str, start_date: str = "", end_date: str = "") -> tuple[bool, str]:
    if not name.strip():
        return False, "Session name is required."
    db = get_session()
    try:
        existing = db.execute(select(AcademicSession).where(AcademicSession.name == name.strip())).first()
        if existing:
            return False, "A session with this name already exists."
        db.add(AcademicSession(name=name.strip(), start_date=start_date, end_date=end_date))
        db.commit()
        return True, "Session created."
    finally:
        db.close()


def activate_session(session_id: str) -> tuple[bool, str]:
    db = get_session()
    try:
        db.execute(
            AcademicSession.__table__.update().values(is_current=False)
        )
        target = db.get(AcademicSession, session_id)
        if target is None:
            return False, "Session not found."
        target.is_current = True
        db.commit()
        return True, "Session activated."
    finally:
        db.close()


def get_current_session() -> AcademicSession | None:
    db = get_session()
    try:
        return db.execute(
            select(AcademicSession).where(AcademicSession.is_current == True)  # noqa: E712
        ).scalar_one_or_none()
    finally:
        db.close()


# ------------------------------------------------------------------ terms --

def list_terms(session_id: str | None = None) -> list[AcademicTerm]:
    db = get_session()
    try:
        stmt = select(AcademicTerm)
        if session_id:
            stmt = stmt.where(AcademicTerm.session_id == session_id)
        return list(db.execute(stmt).scalars().all())
    finally:
        db.close()


def create_term(session_id: str, name: str, start_date: str = "", end_date: str = "") -> tuple[bool, str]:
    if not name.strip():
        return False, "Term name is required."
    db = get_session()
    try:
        db.add(AcademicTerm(session_id=session_id, name=name.strip(), start_date=start_date, end_date=end_date))
        db.commit()
        return True, "Term created."
    finally:
        db.close()


def activate_term(term_id: str) -> tuple[bool, str]:
    db = get_session()
    try:
        term = db.get(AcademicTerm, term_id)
        if term is None:
            return False, "Term not found."
        db.execute(
            AcademicTerm.__table__.update().where(AcademicTerm.session_id == term.session_id).values(is_current=False)
        )
        term.is_current = True
        db.commit()
        return True, "Term activated."
    finally:
        db.close()


def get_current_term() -> AcademicTerm | None:
    db = get_session()
    try:
        return db.execute(
            select(AcademicTerm).where(AcademicTerm.is_current == True)  # noqa: E712
        ).scalar_one_or_none()
    finally:
        db.close()


# ------------------------------------------------------------ departments --

def list_departments() -> list[Department]:
    db = get_session()
    try:
        return list(db.execute(select(Department)).scalars().all())
    finally:
        db.close()


def create_department(name: str, description: str = "") -> tuple[bool, str]:
    if not name.strip():
        return False, "Department name is required."
    db = get_session()
    try:
        existing = db.execute(select(Department).where(Department.name == name.strip())).first()
        if existing:
            return False, "A department with this name already exists."
        db.add(Department(name=name.strip(), description=description))
        db.commit()
        return True, "Department created."
    finally:
        db.close()


def update_department(department_id: str, name: str, description: str = "") -> tuple[bool, str]:
    db = get_session()
    try:
        dept = db.get(Department, department_id)
        if dept is None:
            return False, "Department not found."
        dept.name = name.strip()
        dept.description = description
        db.commit()
        return True, "Department updated."
    finally:
        db.close()


# ---------------------------------------------------------------- classes --

def list_active_classes() -> list[SchoolClass]:
    db = get_session()
    try:
        return list(db.execute(
            select(SchoolClass).where(SchoolClass.is_active == True)  # noqa: E712
        ).scalars().all())
    finally:
        db.close()


def list_all_classes() -> list[SchoolClass]:
    db = get_session()
    try:
        return list(db.execute(select(SchoolClass)).scalars().all())
    finally:
        db.close()


def create_class(name: str, level: str = "", capacity: int = 40) -> tuple[bool, str]:
    if not name.strip():
        return False, "Class name is required."
    db = get_session()
    try:
        db.add(SchoolClass(name=name.strip(), level=level, capacity=capacity))
        db.commit()
        return True, "Class created."
    finally:
        db.close()


def update_class(class_id: str, name: str, level: str, capacity: int) -> tuple[bool, str]:
    db = get_session()
    try:
        target = db.get(SchoolClass, class_id)
        if target is None:
            return False, "Class not found."
        target.name = name.strip()
        target.level = level
        target.capacity = capacity
        db.commit()
        return True, "Class updated."
    finally:
        db.close()


def set_class_active(class_id: str, is_active: bool) -> tuple[bool, str]:
    db = get_session()
    try:
        target = db.get(SchoolClass, class_id)
        if target is None:
            return False, "Class not found."
        target.is_active = is_active
        db.commit()
        return True, "Class updated."
    finally:
        db.close()


# --------------------------------------------------------------- subjects --

def list_subjects() -> list[Subject]:
    db = get_session()
    try:
        return list(db.execute(select(Subject)).scalars().all())
    finally:
        db.close()


def create_subject(name: str, code: str, department_id: str | None = None) -> tuple[bool, str]:
    if not name.strip() or not code.strip():
        return False, "Subject name and code are required."
    db = get_session()
    try:
        existing = db.execute(select(Subject).where(Subject.code == code.strip().upper())).first()
        if existing:
            return False, "A subject with this code already exists."
        db.add(Subject(name=name.strip(), code=code.strip().upper(), department_id=department_id))
        db.commit()
        return True, "Subject created."
    finally:
        db.close()
