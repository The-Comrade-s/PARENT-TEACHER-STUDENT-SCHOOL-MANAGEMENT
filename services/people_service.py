"""
Student, parent, and teacher management.

Registration is handled in auth_service.py; this module covers everything
after account creation: profile edits, search/filter, deactivation and
restoration, and parent-child linking.
"""

from sqlalchemy import select

from auth.security import hash_password
from database.connection import get_session
from models.people import StudentProfile, ParentProfile, TeacherProfile, ParentStudentLink
from models.school import SchoolClass
from models.user import User, Role
from permissions.rbac import ROLE_STUDENT


# --------------------------------------------------------------- students --

def create_student(
    first_name: str, last_name: str, admission_number: str, class_id: str | None = None,
    date_of_birth=None, gender: str = "", emergency_name: str = "", emergency_phone: str = "",
    create_login: bool = False, email: str = "", password: str = "",
) -> tuple[bool, str]:
    if not first_name.strip() or not last_name.strip() or not admission_number.strip():
        return False, "First name, last name, and admission number are required."

    db = get_session()
    try:
        existing = db.execute(
            select(StudentProfile).where(StudentProfile.admission_number == admission_number.strip())
        ).first()
        if existing:
            return False, "A student with this admission number already exists."

        user_id = None
        if create_login:
            if not email.strip() or not password:
                return False, "Email and password are required to create a student login."
            if db.execute(select(User).where(User.email == email.strip().lower())).first():
                return False, "An account with this email already exists."
            role = db.execute(select(Role).where(Role.name == ROLE_STUDENT)).scalar_one()
            user = User(
                first_name=first_name.strip(),
                last_name=last_name.strip(),
                email=email.strip().lower(),
                hashed_password=hash_password(password),
                gender=gender or None,
                date_of_birth=date_of_birth,
                status="active",
            )
            user.roles.append(role)
            db.add(user)
            db.flush()
            user_id = user.id

        student = StudentProfile(
            user_id=user_id,
            admission_number=admission_number.strip(),
            current_class_id=class_id,
            emergency_contact_name=emergency_name or None,
            emergency_contact_phone=emergency_phone or None,
        )
        db.add(student)
        db.commit()
        return True, "Student created."
    finally:
        db.close()


def list_students(search: str = "", class_id: str | None = None, status: str | None = None) -> list[dict]:
    db = get_session()
    try:
        stmt = select(StudentProfile)
        if class_id:
            stmt = stmt.where(StudentProfile.current_class_id == class_id)
        if status:
            stmt = stmt.where(StudentProfile.student_status == status)
        students = db.execute(stmt).scalars().all()

        results = []
        for s in students:
            display_name = None
            if s.user_id:
                u = db.get(User, s.user_id)
                display_name = u.full_name if u else None
            class_obj = db.get(SchoolClass, s.current_class_id) if s.current_class_id else None
            row = {
                "id": s.id,
                "name": display_name or s.admission_number,
                "admission_number": s.admission_number,
                "class_name": class_obj.name if class_obj else "Unassigned",
                "status": s.student_status,
                "is_active": s.is_active,
            }
            if search:
                haystack = f"{row['name']} {row['admission_number']}".lower()
                if search.lower() not in haystack:
                    continue
            results.append(row)
        return results
    finally:
        db.close()


def update_student_class(student_id: str, class_id: str | None) -> tuple[bool, str]:
    db = get_session()
    try:
        student = db.get(StudentProfile, student_id)
        if student is None:
            return False, "Student not found."
        student.current_class_id = class_id
        db.commit()
        return True, "Student class updated."
    finally:
        db.close()


def set_student_status(student_id: str, status: str) -> tuple[bool, str]:
    """status: active, inactive, graduated"""
    db = get_session()
    try:
        student = db.get(StudentProfile, student_id)
        if student is None:
            return False, "Student not found."
        student.student_status = status
        student.is_active = status == "active"
        db.commit()
        return True, "Student status updated."
    finally:
        db.close()


# --------------------------------------------------------- parent linking --

def link_parent_to_student(parent_profile_id: str, student_profile_id: str, is_primary: bool = False) -> tuple[bool, str]:
    db = get_session()
    try:
        existing = db.execute(
            select(ParentStudentLink).where(
                ParentStudentLink.parent_id == parent_profile_id,
                ParentStudentLink.student_id == student_profile_id,
            )
        ).first()
        if existing:
            return False, "This parent is already linked to this student."
        db.add(ParentStudentLink(
            parent_id=parent_profile_id, student_id=student_profile_id, is_primary_guardian=is_primary
        ))
        db.commit()
        return True, "Parent linked to student."
    finally:
        db.close()


def unlink_parent_from_student(link_id: str) -> tuple[bool, str]:
    db = get_session()
    try:
        link = db.get(ParentStudentLink, link_id)
        if link is None:
            return False, "Link not found."
        db.delete(link)
        db.commit()
        return True, "Parent unlinked from student."
    finally:
        db.close()


def list_parents(search: str = "") -> list[dict]:
    db = get_session()
    try:
        rows = db.execute(select(ParentProfile, User).join(User, ParentProfile.user_id == User.id)).all()
        results = []
        for profile, user in rows:
            if search and search.lower() not in f"{user.full_name} {user.email}".lower():
                continue
            children_count = len(profile.children_links)
            results.append({
                "id": profile.id,
                "user_id": user.id,
                "name": user.full_name,
                "email": user.email,
                "children_count": children_count,
                "is_active": user.status == "active",
            })
        return results
    finally:
        db.close()


def list_students_for_linking() -> list[dict]:
    db = get_session()
    try:
        students = db.execute(select(StudentProfile)).scalars().all()
        return [{"id": s.id, "label": f"{s.admission_number}"} for s in students]
    finally:
        db.close()


# -------------------------------------------------------------- teachers --

def list_teachers(search: str = "", approval_status: str | None = None) -> list[dict]:
    db = get_session()
    try:
        stmt = select(TeacherProfile, User).join(User, TeacherProfile.user_id == User.id)
        if approval_status:
            stmt = stmt.where(TeacherProfile.approval_status == approval_status)
        rows = db.execute(stmt).all()
        results = []
        for profile, user in rows:
            if search and search.lower() not in f"{user.full_name} {user.email}".lower():
                continue
            assigned_class = db.execute(
                select(SchoolClass).where(SchoolClass.class_teacher_id == profile.id)
            ).scalar_one_or_none()
            results.append({
                "id": profile.id,
                "user_id": user.id,
                "name": user.full_name,
                "email": user.email,
                "employee_id": profile.employee_id,
                "employment_status": profile.employment_status,
                "approval_status": profile.approval_status,
                "assigned_class_name": assigned_class.name if assigned_class else None,
            })
        return results
    finally:
        db.close()


def update_teacher_profile(
    teacher_profile_id: str, employee_id: str = "", qualification: str = "",
    department_id: str | None = None, employment_status: str | None = None,
) -> tuple[bool, str]:
    db = get_session()
    try:
        profile = db.get(TeacherProfile, teacher_profile_id)
        if profile is None:
            return False, "Teacher profile not found."
        if employee_id:
            profile.employee_id = employee_id
        if qualification:
            profile.qualification = qualification
        if department_id is not None:
            profile.department_id = department_id
        if employment_status:
            profile.employment_status = employment_status
        db.commit()
        return True, "Teacher profile updated."
    finally:
        db.close()
