import streamlit as st
from sqlalchemy import select

from components.ui import page_header, metric_row, load_theme, empty_state
from database.connection import get_session
from models.people import StudentProfile
from permissions.rbac import require_role, ROLE_STUDENT


def render():
    user = require_role(ROLE_STUDENT)
    load_theme()
    page_header("Student Dashboard", f"Welcome, {user.full_name}")

    db = get_session()
    try:
        profile = db.execute(
            select(StudentProfile).where(StudentProfile.user_id == user.id)
        ).scalar_one_or_none()
        # Relationship access must happen here, while the session is still open.
        class_name = (profile.current_class.name if profile and profile.current_class else "Unassigned")
    finally:
        db.close()

    if profile is None:
        empty_state("Your student profile could not be found. Contact an administrator.")
        return

    metric_row([
        ("Current Class", class_name),
        ("Attendance Rate", "N/A"),
        ("Pending Assignments", "0"),
        ("Notifications", "0"),
    ])

    st.info("Academic results, assignments, attendance, and messaging are added in later phases.")
