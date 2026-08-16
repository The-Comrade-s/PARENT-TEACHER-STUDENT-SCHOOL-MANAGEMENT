import streamlit as st

from components.ui import page_header, load_theme, empty_state
from permissions.rbac import require_role, ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN
from services import export_service, school_service


def render():
    user = require_role(ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN)
    load_theme()
    page_header("Reports & Exports")

    tabs = st.tabs(["Students", "Class Results", "Export History"])

    with tabs[0]:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Export Students (CSV)"):
                data = export_service.export_students_csv(user.id)
                st.download_button("Download CSV", data=data, file_name="students.csv", mime="text/csv")
        with col2:
            if st.button("Export Students (Excel)"):
                data = export_service.export_students_excel(user.id)
                st.download_button(
                    "Download Excel", data=data, file_name="students.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

    with tabs[1]:
        classes = school_service.list_active_classes()
        subjects = school_service.list_subjects()
        term = school_service.get_current_term()
        if not classes or not subjects or term is None:
            empty_state("Set up classes, subjects, and an active term before exporting results.")
        else:
            class_options = {c.name: c.id for c in classes}
            subject_options = {s.name: s.id for s in subjects}
            class_label = st.selectbox("Class", list(class_options.keys()))
            subject_label = st.selectbox("Subject", list(subject_options.keys()))
            if st.button("Export Results (CSV)"):
                data = export_service.export_class_results_csv(
                    user.id, class_options[class_label], subject_options[subject_label], term.id
                )
                st.download_button("Download CSV", data=data, file_name="results.csv", mime="text/csv")

    with tabs[2]:
        history = export_service.list_export_history()
        if not history:
            empty_state("No exports recorded yet.")
        else:
            st.table([{
                "Time": h.created_at.strftime("%Y-%m-%d %H:%M"), "Type": h.export_type,
                "Module": h.module, "File": h.file_name,
            } for h in history])
