import streamlit as st
from sqlalchemy import select

from components.ui import page_header, metric_row, load_theme, empty_state
from database.connection import get_session
from models.people import ParentProfile, ParentStudentLink, StudentProfile
from permissions.rbac import require_role, ROLE_PARENT


def render():
    user = require_role(ROLE_PARENT)
    load_theme()
    page_header("Parent Dashboard", f"Welcome, {user.full_name}")

    db = get_session()
    try:
        profile = db.execute(
            select(ParentProfile).where(ParentProfile.user_id == user.id)
        ).scalar_one_or_none()
        children = []
        if profile is not None:
            links = db.execute(
                select(ParentStudentLink).where(ParentStudentLink.parent_id == profile.id)
            ).scalars().all()
            for link in links:
                student = db.get(StudentProfile, link.student_id)
                if student:
                    children.append(student)
    finally:
        db.close()

    metric_row([
        ("Linked Children", str(len(children))),
        ("Upcoming Meetings", "0"),
        ("Unread Messages", "0"),
        ("Notifications", "0"),
    ])

    st.subheader("Your Children")
    if children:
        for child in children:
            st.markdown(
                f'<div class="ptms-card">Admission No: {child.admission_number} &middot; '
                f'Status: {child.student_status}</div>',
                unsafe_allow_html=True,
            )
    else:
        empty_state("No children are linked to your account yet. Contact the school administrator to link a child.")

    st.info("Attendance, academic performance, assignments, and messaging are added in later phases.")
