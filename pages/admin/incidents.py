import streamlit as st

from components.ui import page_header, load_theme, empty_state
from permissions.rbac import require_role, ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN
from services import security_service, people_service


def render():
    user = require_role(ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN)
    load_theme()
    page_header("Incidents")

    students = people_service.list_students()
    student_options = {"None": None}
    student_options.update({f"{s['name']} ({s['admission_number']})": s["id"] for s in students})

    with st.form("report_incident_form"):
        description = st.text_area("Description")
        col1, col2, col3 = st.columns(3)
        with col1:
            location = st.text_input("Location")
        with col2:
            severity = st.selectbox("Severity", ["low", "medium", "high"])
        with col3:
            student_label = st.selectbox("Related Student", list(student_options.keys()))
        if st.form_submit_button("Report Incident", type="primary"):
            ok, message = security_service.report_incident(
                user.id, description, location, student_options[student_label], severity
            )
            st.success(message) if ok else st.error(message)
            if ok:
                st.rerun()

    incidents = security_service.list_incidents()
    if not incidents:
        empty_state("No incidents reported yet.")
        return

    for i in incidents:
        st.markdown('<div class="ptms-card">', unsafe_allow_html=True)
        st.write(f"{i.severity.title()} &middot; {i.status.title()} &middot; {i.location or 'No location'}")
        st.write(i.description)
        if i.status != "resolved":
            new_status = st.selectbox(
                "Update status", ["open", "investigating", "resolved"],
                index=["open", "investigating", "resolved"].index(i.status), key=f"status_{i.id}",
            )
            if st.button("Save Status", key=f"save_status_{i.id}"):
                security_service.update_incident_status(i.id, new_status)
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
