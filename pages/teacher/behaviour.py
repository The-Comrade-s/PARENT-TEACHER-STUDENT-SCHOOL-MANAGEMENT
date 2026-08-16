import streamlit as st
from sqlalchemy import select

from components.ui import page_header, load_theme, empty_state
from database.connection import get_session
from models.people import TeacherProfile
from permissions.rbac import require_role, ROLE_TEACHER
from services import behaviour_service, notification_service


def render():
    user = require_role(ROLE_TEACHER)
    load_theme()
    page_header("Behaviour Records")

    db = get_session()
    try:
        profile = db.execute(select(TeacherProfile).where(TeacherProfile.user_id == user.id)).scalar_one_or_none()
        classes = profile.classes_as_teacher if profile else []
        roster = []
        for c in classes:
            roster.extend(c.students)
    finally:
        db.close()

    if not roster:
        empty_state("You are not currently assigned as a class teacher for any class.")
        return

    student_options = {s.admission_number: s for s in roster}
    student_label = st.selectbox("Student", list(student_options.keys()))
    student = student_options[student_label]

    with st.form("behaviour_form"):
        category = st.radio("Category", ["positive", "negative"], horizontal=True)
        description = st.text_area("Description")
        disciplinary_action = st.text_input("Disciplinary Action (if applicable)")
        notify_parent = st.checkbox("Notify parent")
        if st.form_submit_button("Save Record", type="primary"):
            ok, message = behaviour_service.create_behaviour_record(
                student.id, user.id, category, description, disciplinary_action
            )
            if ok and notify_parent:
                for link in student.parent_links:
                    parent_user_id = link.parent.user_id
                    notification_service.create_notification(
                        parent_user_id, "New behaviour record",
                        f"A {category} behaviour record was added for {student.admission_number}.",
                    )
            st.success(message) if ok else st.error(message)
            if ok:
                st.rerun()

    st.divider()
    st.subheader("History")
    records = behaviour_service.list_behaviour_records(student.id)
    if not records:
        empty_state("No behaviour records for this student yet.")
        return
    for r in records:
        st.markdown(
            f'<div class="ptms-card"><strong>{r.category.title()}</strong> &middot; {r.action_status}<br>'
            f'{r.description}<br><small>{r.created_at.strftime("%Y-%m-%d")}</small></div>',
            unsafe_allow_html=True,
        )
        if r.action_status == "open" and st.button("Mark Resolved", key=f"resolve_{r.id}"):
            behaviour_service.resolve_behaviour_record(r.id)
            st.rerun()
