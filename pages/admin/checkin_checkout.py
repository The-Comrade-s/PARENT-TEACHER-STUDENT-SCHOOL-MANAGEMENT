import streamlit as st

from components.ui import page_header, load_theme, empty_state
from permissions.rbac import require_role, ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN
from services import security_service, people_service


def render():
    user = require_role(ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN)
    load_theme()
    page_header("Check-In / Check-Out", "Record student arrivals, departures, and pickup verification")

    students = people_service.list_students()
    if not students:
        empty_state("No students found.")
        return
    student_options = {f"{s['name']} ({s['admission_number']})": s["id"] for s in students}

    tabs = st.tabs(["Check-In / Check-Out", "Pickup Verification", "Recent Activity"])

    with tabs[0]:
        with st.form("checkinout_form"):
            student_label = st.selectbox("Student", list(student_options.keys()))
            notes = st.text_input("Notes (optional)")
            col1, col2 = st.columns(2)
            with col1:
                check_in_clicked = st.form_submit_button("Check In", type="primary")
            with col2:
                check_out_clicked = st.form_submit_button("Check Out")
        if check_in_clicked:
            ok, message = security_service.check_in_student(student_options[student_label], user.id, notes)
            st.success(message) if ok else st.error(message)
        if check_out_clicked:
            ok, message = security_service.check_out_student(student_options[student_label], user.id, notes)
            st.success(message) if ok else st.error(message)

    with tabs[1]:
        student_label = st.selectbox("Student for pickup", list(student_options.keys()), key="pickup_student")
        student_id = student_options[student_label]

        with st.expander("Create a new pickup authorization"):
            person_name = st.text_input("Authorized Person Name")
            if st.button("Generate Pickup PIN"):
                ok, message, pin = security_service.create_pickup_authorization(student_id, user.id, person_name)
                if ok:
                    st.success(f"{message} PIN: {pin}")
                else:
                    st.error(message)

        with st.form("verify_pickup_form"):
            pin_input = st.text_input("Enter PIN to verify pickup")
            if st.form_submit_button("Verify Pickup"):
                ok, message = security_service.verify_pickup_pin(student_id, pin_input, user.id)
                st.success(message) if ok else st.error(message)

    with tabs[2]:
        records = security_service.list_check_records()
        if not records:
            empty_state("No check-in/check-out activity recorded yet.")
        for r in records:
            st.markdown(
                f'<div class="ptms-card">{r.check_type.upper()} &middot; '
                f'{r.recorded_at.strftime("%Y-%m-%d %H:%M") if r.recorded_at else ""}<br>{r.notes or ""}</div>',
                unsafe_allow_html=True,
            )
