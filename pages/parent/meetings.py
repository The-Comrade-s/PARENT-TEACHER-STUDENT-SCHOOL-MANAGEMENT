import streamlit as st
from sqlalchemy import select

from components.ui import page_header, load_theme, empty_state
from database.connection import get_session
from models.people import ParentProfile, ParentStudentLink, StudentProfile
from permissions.rbac import require_role, ROLE_PARENT
from services import meeting_service, notification_service


def render():
    user = require_role(ROLE_PARENT)
    load_theme()
    page_header("Parent-Teacher Meetings")

    db = get_session()
    try:
        profile = db.execute(select(ParentProfile).where(ParentProfile.user_id == user.id)).scalar_one_or_none()
        children = []
        if profile:
            links = db.execute(select(ParentStudentLink).where(ParentStudentLink.parent_id == profile.id)).scalars().all()
            for link in links:
                student = db.get(StudentProfile, link.student_id)
                if student:
                    children.append(student)
    finally:
        db.close()

    if not children:
        empty_state("No children are linked to your account yet.")
        return

    child_options = {c.admission_number: c for c in children}
    with st.form("meeting_request_form"):
        child_label = st.selectbox("Child", list(child_options.keys()))
        reason = st.text_area("Reason for meeting")
        requested_time = st.text_input("Preferred date/time (optional)")
        if st.form_submit_button("Request Meeting", type="primary"):
            child = child_options[child_label]
            teacher_id = child.current_class.class_teacher_id if child.current_class else None
            ok, message = meeting_service.request_meeting(user.id, teacher_id, child.id, reason)
            if ok and teacher_id:
                teacher_user_id = child.current_class.class_teacher.user_id
                notification_service.create_notification(
                    teacher_user_id, "New meeting request", f"A parent requested a meeting about {child.admission_number}."
                )
            st.success(message) if ok else st.error(message)
            if ok:
                st.rerun()

    st.divider()
    meetings = meeting_service.list_meetings_for_user(user.id)
    if not meetings:
        empty_state("You have not requested any meetings yet.")
        return
    for m in meetings:
        st.markdown(
            f'<div class="ptms-card">Status: {m.status.title()}<br>{m.reason or ""}<br>'
            f'<small>{m.created_at.strftime("%Y-%m-%d")}</small></div>',
            unsafe_allow_html=True,
        )
