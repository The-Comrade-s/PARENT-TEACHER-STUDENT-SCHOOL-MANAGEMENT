import streamlit as st

from components.ui import page_header, load_theme, empty_state
from permissions.rbac import require_role, ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN
from services import security_service, people_service


def render():
    user = require_role(ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN)
    load_theme()
    page_header("Student Movements", "Track students leaving and returning during the day")

    students = people_service.list_students()
    student_options = {f"{s['name']} ({s['admission_number']})": s["id"] for s in students}

    with st.form("log_movement_form"):
        student_label = st.selectbox("Student", list(student_options.keys()))
        destination = st.text_input("Destination (e.g. clinic, library)")
        if st.form_submit_button("Log Movement", type="primary"):
            ok, message = security_service.log_movement(student_options[student_label], destination, user.id)
            st.success(message) if ok else st.error(message)
            if ok:
                st.rerun()

    st.subheader("Currently Out")
    open_movements = security_service.list_open_movements()
    if not open_movements:
        empty_state("No students are currently logged as out.")
        return

    for m in open_movements:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"{m.destination} &middot; departed {m.departed_at}")
        with col2:
            if st.button("Mark Returned", key=f"return_{m.id}"):
                security_service.return_student(m.id)
                st.rerun()
