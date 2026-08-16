import streamlit as st

from components.ui import page_header, load_theme, empty_state
from permissions.rbac import require_role, ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN
from services import meeting_service


def render():
    user = require_role(ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN)
    load_theme()
    page_header("PTA Meetings")

    with st.form("new_pta_meeting_form"):
        title = st.text_input("Meeting Title")
        if st.form_submit_button("Create PTA Meeting", type="primary"):
            ok, message = meeting_service.create_pta_meeting(user.id, title)
            st.success(message) if ok else st.error(message)
            if ok:
                st.rerun()

    meetings = meeting_service.list_pta_meetings()
    if not meetings:
        empty_state("No PTA meetings recorded yet.")
        return

    for m in meetings:
        with st.expander(m.title):
            minutes = st.text_area("Minutes", value=m.minutes or "", key=f"minutes_{m.id}")
            if st.button("Save Minutes", key=f"save_minutes_{m.id}"):
                meeting_service.record_pta_minutes(m.id, minutes)
                st.success("Minutes saved.")
