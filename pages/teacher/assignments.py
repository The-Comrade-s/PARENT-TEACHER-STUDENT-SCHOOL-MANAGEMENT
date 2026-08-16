import streamlit as st
from sqlalchemy import select

from components.ui import page_header, load_theme, empty_state
from database.connection import get_session
from models.people import TeacherProfile
from permissions.rbac import require_role, ROLE_TEACHER
from services import assignment_service, school_service


def render():
    user = require_role(ROLE_TEACHER)
    load_theme()
    page_header("Assignments", "Create assignments and review submissions")

    db = get_session()
    try:
        profile = db.execute(select(TeacherProfile).where(TeacherProfile.user_id == user.id)).scalar_one_or_none()
        classes = profile.classes_as_teacher if profile else []
    finally:
        db.close()

    if not classes:
        empty_state("You are not currently assigned as a class teacher for any class.")
        return

    class_options = {c.name: c.id for c in classes}
    class_label = st.selectbox("Class", list(class_options.keys()))
    class_id = class_options[class_label]

    subjects = school_service.list_subjects()
    subject_options = {"None": None}
    subject_options.update({s.name: s.id for s in subjects})

    with st.expander("Create a new assignment"):
        with st.form("new_assignment_form"):
            title = st.text_input("Title")
            description = st.text_area("Description")
            subject_label = st.selectbox("Subject", list(subject_options.keys()))
            due_date = st.date_input("Due Date")
            if st.form_submit_button("Create Assignment", type="primary"):
                ok, message = assignment_service.create_assignment(
                    class_id, profile.id, title, description, subject_options[subject_label], due_date
                )
                st.success(message) if ok else st.error(message)
                if ok:
                    st.rerun()

    assignments = assignment_service.list_assignments_for_class(class_id)
    if not assignments:
        empty_state("No assignments created for this class yet.")
        return

    for a in assignments:
        with st.expander(f"{a.title} (due {a.due_date})"):
            st.write(a.description or "No description provided.")
            submissions = assignment_service.list_submissions_for_assignment(a.id)
            for s in submissions:
                col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                with col1:
                    st.write(s["student_admission_number"])
                with col2:
                    st.caption(s["status"])
                with col3:
                    score_input = st.number_input(
                        "Score", min_value=0.0, max_value=100.0,
                        value=float(s["score"]) if s["score"] is not None else 0.0,
                        key=f"score_{s['submission_id']}",
                    )
                with col4:
                    if st.button("Save", key=f"save_score_{s['submission_id']}"):
                        assignment_service.review_submission(s["submission_id"], score_input)
                        st.rerun()
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Delete Assignment", key=f"delete_assignment_{a.id}"):
                    assignment_service.delete_assignment(a.id)
                    st.rerun()
