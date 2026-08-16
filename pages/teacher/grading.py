import streamlit as st
from sqlalchemy import select

from components.ui import page_header, load_theme, empty_state
from database.connection import get_session
from models.people import TeacherProfile
from permissions.rbac import require_role, ROLE_TEACHER
from services import results_service, school_service


def render():
    user = require_role(ROLE_TEACHER)
    load_theme()
    page_header("Grading", "Enter continuous assessment and examination scores")

    results_service.ensure_default_grading_setup()

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
    if not subjects:
        empty_state("No subjects have been created yet.")
        return
    subject_options = {s.name: s.id for s in subjects}
    subject_label = st.selectbox("Subject", list(subject_options.keys()))
    subject_id = subject_options[subject_label]

    term = school_service.get_current_term()
    if term is None:
        st.warning("No academic term is currently active. Ask an administrator to activate one.")
        return

    rows = results_service.get_class_results(class_id, subject_id, term.id)
    if not rows:
        empty_state("No active students found in this class.")
        return

    with st.form("grading_form"):
        entries = {}
        for row in rows:
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.write(row["admission_number"])
            with col2:
                ca = st.number_input(
                    "CA", min_value=0.0, max_value=40.0, value=float(row["ca_score"]),
                    key=f"ca_{row['student_id']}",
                )
            with col3:
                exam = st.number_input(
                    "Exam", min_value=0.0, max_value=60.0, value=float(row["exam_score"]),
                    key=f"exam_{row['student_id']}",
                )
            entries[row["student_id"]] = (ca, exam)

        if st.form_submit_button("Save Scores", type="primary"):
            for student_id, (ca, exam) in entries.items():
                results_service.enter_score(student_id, class_id, subject_id, term.id, profile.id, ca, exam)
            st.success("Scores saved.")
            st.rerun()

    if st.button("Submit results for admin review"):
        ok, message = results_service.submit_results_for_review(class_id, subject_id, term.id)
        st.success(message) if ok else st.error(message)
