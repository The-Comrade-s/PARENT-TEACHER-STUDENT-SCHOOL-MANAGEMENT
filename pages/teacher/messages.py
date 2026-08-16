import streamlit as st
from sqlalchemy import select

from components.ui import page_header, load_theme
from components.messaging_ui import render_messaging
from database.connection import get_session
from models.people import TeacherProfile, ParentStudentLink, ParentProfile
from models.user import User, Role
from permissions.rbac import require_role, ROLE_TEACHER, ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN


def render():
    user = require_role(ROLE_TEACHER)
    load_theme()
    page_header("Messages")

    db = get_session()
    try:
        profile = db.execute(select(TeacherProfile).where(TeacherProfile.user_id == user.id)).scalar_one_or_none()
        contacts = {}

        if profile:
            for school_class in profile.classes_as_teacher:
                for student in school_class.students:
                    for link in student.parent_links:
                        parent_user = db.get(User, link.parent.user_id)
                        if parent_user:
                            contacts[f"{parent_user.full_name} (parent)"] = parent_user.id

        admins = db.execute(
            select(User).join(User.roles).where(Role.name.in_([ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN]))
        ).unique().scalars().all()
        for a in admins:
            contacts[f"{a.full_name} (admin)"] = a.id
    finally:
        db.close()

    render_messaging(user.id, contacts)
