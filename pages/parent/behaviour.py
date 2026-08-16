import streamlit as st
from sqlalchemy import select

from components.ui import page_header, load_theme, empty_state
from database.connection import get_session
from models.people import ParentProfile, ParentStudentLink, StudentProfile
from permissions.rbac import require_role, ROLE_PARENT
from services import behaviour_service


def render():
    user = require_role(ROLE_PARENT)
    load_theme()
    page_header("Children's Behaviour Records")

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
    child_label = st.selectbox("Child", list(child_options.keys()))
    child = child_options[child_label]

    summary = behaviour_service.behaviour_summary(child.id)
    st.caption(f"Total: {summary['total']} &middot; Positive: {summary['positive']} &middot; Negative: {summary['negative']}")

    records = behaviour_service.list_behaviour_records(child.id)
    if not records:
        empty_state("No behaviour records for this child yet.")
        return
    for r in records:
        st.markdown(
            f'<div class="ptms-card"><strong>{r.category.title()}</strong><br>{r.description}<br>'
            f'<small>{r.created_at.strftime("%Y-%m-%d")}</small></div>',
            unsafe_allow_html=True,
        )
