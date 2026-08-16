import streamlit as st
from sqlalchemy import select

from components.ui import page_header, load_theme
from components.messaging_ui import render_messaging
from database.connection import get_session
from models.user import User, Role
from permissions.rbac import require_role, ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN, ROLE_TEACHER, ROLE_PARENT


def render():
    user = require_role(ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN)
    load_theme()
    page_header("Messages")

    db = get_session()
    try:
        contacts = {}
        others = db.execute(
            select(User).join(User.roles).where(Role.name.in_([ROLE_TEACHER, ROLE_PARENT]))
        ).unique().scalars().all()
        for o in others:
            role_label = "teacher" if o.has_role(ROLE_TEACHER) else "parent"
            contacts[f"{o.full_name} ({role_label})"] = o.id
    finally:
        db.close()

    render_messaging(user.id, contacts)
