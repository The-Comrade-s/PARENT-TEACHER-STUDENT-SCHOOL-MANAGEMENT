import streamlit as st
from sqlalchemy import select

from components.ui import page_header, metric_row, load_theme, empty_state
from database.connection import get_session
from models.people import TeacherProfile
from permissions.rbac import require_role, ROLE_TEACHER


def render():
    user = require_role(ROLE_TEACHER)
    load_theme()
    page_header("Teacher Dashboard", f"Welcome, {user.full_name}")

    db = get_session()
    try:
        profile = db.execute(
            select(TeacherProfile).where(TeacherProfile.user_id == user.id)
        ).scalar_one_or_none()
    finally:
        db.close()

    if profile is None:
        empty_state("Your teacher profile could not be found. Contact an administrator.")
        return

    if profile.approval_status == "pending":
        st.warning("Your account is pending administrator approval. Some features are unavailable until then.")
        return

    assigned_classes = profile.classes_as_teacher
    metric_row([
        ("Assigned Classes", str(len(assigned_classes))),
        ("Assigned Subjects", "0"),
        ("Pending Assignments", "0"),
        ("Unread Messages", "0"),
    ])

    st.subheader("Your Classes")
    if assigned_classes:
        for c in assigned_classes:
            st.markdown(f'<div class="ptms-card">{c.name}</div>', unsafe_allow_html=True)
    else:
        empty_state("You are not currently assigned as a class teacher for any class.")

    st.info("Attendance, grading, behaviour, and messaging tools are added in later phases.")
