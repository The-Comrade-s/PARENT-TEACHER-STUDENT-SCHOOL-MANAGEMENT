import streamlit as st
from sqlalchemy import select

from components.ui import page_header, load_theme, empty_state
from database.connection import get_session
from models.people import StudentProfile
from permissions.rbac import require_role, ROLE_STUDENT
from services import assignment_service


def render():
    user = require_role(ROLE_STUDENT)
    load_theme()
    page_header("My Assignments")

    db = get_session()
    try:
        profile = db.execute(select(StudentProfile).where(StudentProfile.user_id == user.id)).scalar_one_or_none()
    finally:
        db.close()

    if profile is None or profile.current_class_id is None:
        empty_state("You are not currently assigned to a class.")
        return

    assignments = assignment_service.list_assignments_for_student(profile.id, profile.current_class_id)
    if not assignments:
        empty_state("No assignments have been posted for your class yet.")
        return

    for a in assignments:
        with st.expander(f"{a['title']} (due {a['due_date']}) - {a['submission_status']}"):
            st.write(a["description"] or "No description provided.")
            if a["score"] is not None:
                st.metric("Score", a["score"])
            if a["submission_status"] in ("not_submitted",):
                text = st.text_area("Your submission", key=f"submission_{a['id']}")
                if st.button("Submit", key=f"submit_btn_{a['id']}"):
                    ok, message = assignment_service.submit_assignment(a["submission_id"], text)
                    st.success(message) if ok else st.error(message)
                    st.rerun()
