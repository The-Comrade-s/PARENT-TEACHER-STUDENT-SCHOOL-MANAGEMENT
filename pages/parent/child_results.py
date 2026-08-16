import streamlit as st
from sqlalchemy import select

from components.ui import page_header, load_theme, empty_state
from database.connection import get_session
from models.people import ParentProfile, ParentStudentLink, StudentProfile
from models.user import User
from permissions.rbac import require_role, ROLE_PARENT
from services import school_service
from reports.report_card import generate_report_card_pdf


def render():
    user = require_role(ROLE_PARENT)
    load_theme()
    page_header("Children's Results")

    db = get_session()
    try:
        profile = db.execute(select(ParentProfile).where(ParentProfile.user_id == user.id)).scalar_one_or_none()
        children = []
        if profile is not None:
            links = db.execute(
                select(ParentStudentLink).where(ParentStudentLink.parent_id == profile.id)
            ).scalars().all()
            for link in links:
                student = db.get(StudentProfile, link.student_id)
                if student:
                    child_user = db.get(User, student.user_id) if student.user_id else None
                    children.append((student, child_user))
    finally:
        db.close()

    if not children:
        empty_state("No children are linked to your account yet.")
        return

    term = school_service.get_current_term()
    session = school_service.get_current_session()

    for student, child_user in children:
        name = child_user.full_name if child_user else student.admission_number
        class_name = student.current_class.name if student.current_class else "Unassigned"
        st.markdown(f'<div class="ptms-card"><strong>{name}</strong> &middot; {class_name}</div>', unsafe_allow_html=True)

        if term is None:
            st.caption("No academic term is currently active.")
            continue

        pdf_bytes = generate_report_card_pdf(
            student.admission_number, name, class_name, student.id,
            term.name, session.name if session else "",
        )
        st.download_button(
            "Download Report Card (PDF)", data=pdf_bytes,
            file_name=f"report_card_{student.admission_number}.pdf", mime="application/pdf",
            key=f"download_{student.id}",
        )
