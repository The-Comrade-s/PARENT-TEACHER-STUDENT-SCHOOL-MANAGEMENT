"""Global search across authorized records, with role-aware scoping."""

from sqlalchemy import select

from database.connection import get_session
from models.people import StudentProfile, TeacherProfile, ParentProfile
from models.school import SchoolClass, Subject
from models.user import User


def global_search(query: str, limit_per_type: int = 10) -> dict[str, list[dict]]:
    if not query.strip():
        return {}
    q = f"%{query.strip()}%"

    db = get_session()
    try:
        students = db.execute(
            select(StudentProfile).where(StudentProfile.admission_number.ilike(q)).limit(limit_per_type)
        ).scalars().all()

        teacher_rows = db.execute(
            select(TeacherProfile, User)
            .join(User, TeacherProfile.user_id == User.id)
            .where(User.first_name.ilike(q) | User.last_name.ilike(q) | User.email.ilike(q))
            .limit(limit_per_type)
        ).all()

        parent_rows = db.execute(
            select(ParentProfile, User)
            .join(User, ParentProfile.user_id == User.id)
            .where(User.first_name.ilike(q) | User.last_name.ilike(q) | User.email.ilike(q))
            .limit(limit_per_type)
        ).all()

        classes = db.execute(select(SchoolClass).where(SchoolClass.name.ilike(q)).limit(limit_per_type)).scalars().all()
        subjects = db.execute(select(Subject).where(Subject.name.ilike(q)).limit(limit_per_type)).scalars().all()

        return {
            "Students": [{"label": s.admission_number, "id": s.id} for s in students],
            "Teachers": [{"label": u.full_name, "id": t.id} for t, u in teacher_rows],
            "Parents": [{"label": u.full_name, "id": p.id} for p, u in parent_rows],
            "Classes": [{"label": c.name, "id": c.id} for c in classes],
            "Subjects": [{"label": s.name, "id": s.id} for s in subjects],
        }
    finally:
        db.close()
