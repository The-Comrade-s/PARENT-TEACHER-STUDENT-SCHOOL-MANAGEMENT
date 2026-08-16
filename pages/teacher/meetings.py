import streamlit as st
from sqlalchemy import select

from components.ui import page_header, load_theme, empty_state
from database.connection import get_session
from models.people import TeacherProfile
from permissions.rbac import require_role, ROLE_TEACHER
from services import meeting_service


def render():
    user = require_role(ROLE_TEACHER)
    load_theme()
    page_header("Meeting Requests")

    db = get_session()
    try:
        profile = db.execute(select(TeacherProfile).where(TeacherProfile.user_id == user.id)).scalar_one_or_none()
    finally:
        db.close()

    if profile is None:
        empty_state("Your teacher profile could not be found.")
        return

    meetings = meeting_service.list_meetings_for_teacher(profile.id)
    if not meetings:
        empty_state("No meeting requests yet.")
        return

    for m in meetings:
        st.markdown('<div class="ptms-card">', unsafe_allow_html=True)
        st.write(f"Status: {m.status.title()}")
        st.write(m.reason or "No reason given.")
        if m.status == "pending":
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Confirm", key=f"confirm_{m.id}"):
                    meeting_service.update_meeting_status(m.id, "confirmed")
                    st.rerun()
            with col2:
                if st.button("Cancel", key=f"cancel_{m.id}"):
                    meeting_service.update_meeting_status(m.id, "cancelled")
                    st.rerun()
        elif m.status == "confirmed":
            if st.button("Mark Completed", key=f"complete_{m.id}"):
                meeting_service.update_meeting_status(m.id, "completed")
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
