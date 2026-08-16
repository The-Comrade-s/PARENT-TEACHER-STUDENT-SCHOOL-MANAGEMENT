import streamlit as st
from sqlalchemy import select

from components.ui import page_header, load_theme
from components.messaging_ui import render_messaging
from database.connection import get_session
from models.people import ParentProfile, ParentStudentLink, StudentProfile
from models.user import User, Role
from permissions.rbac import require_role, ROLE_PARENT, ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN


def render():
    user = require_role(ROLE_PARENT)
    load_theme()
    page_header("Messages")

    db = get_session()
    try:
        profile = db.execute(select(ParentProfile).where(ParentProfile.user_id == user.id)).scalar_one_or_none()
        contacts = {}

        if profile:
            links = db.execute(select(ParentStudentLink).where(ParentStudentLink.parent_id == profile.id)).scalars().all()
            for link in links:
                student = db.get(StudentProfile, link.student_id)
                if student and student.current_class and student.current_class.class_teacher:
                    teacher_user = db.get(User, student.current_class.class_teacher.user_id)
                    if teacher_user:
                        contacts[f"{teacher_user.full_name} (teacher)"] = teacher_user.id

        admins = db.execute(
            select(User).join(User.roles).where(Role.name.in_([ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN]))
        ).unique().scalars().all()
        for a in admins:
            contacts[f"{a.full_name} (admin)"] = a.id
    finally:
        db.close()

    render_messaging(user.id, contacts)
