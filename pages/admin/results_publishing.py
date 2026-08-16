import streamlit as st

from components.ui import page_header, load_theme, empty_state
from permissions.rbac import require_role, ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN
from services import school_service, results_service


def render():
    require_role(ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN)
    load_theme()
    page_header("Result Publishing", "Review submitted results and publish report cards")

    term = school_service.get_current_term()
    if term is None:
        st.warning("No academic term is currently active.")
        return

    classes = school_service.list_active_classes()
    if not classes:
        empty_state("No classes have been created yet.")
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

    rows = results_service.get_class_results(class_id, subject_id, term.id)
    if rows:
        st.table([{
            "Admission No": r["admission_number"], "CA": r["ca_score"], "Exam": r["exam_score"],
            "Total": r["total_score"], "Grade": r["grade"], "Status": r["status"],
        } for r in rows])
    else:
        empty_state("No results entered yet for this subject and term.")

    st.divider()
    if st.button("Publish All Results for This Class and Term", type="primary"):
        ok, message = results_service.publish_results(class_id, term.id)
        st.success(message) if ok else st.error(message)
