import streamlit as st
from sqlalchemy import select

from components.ui import page_header, load_theme, empty_state
from database.connection import get_session
from models.people import StudentProfile
from permissions.rbac import require_role, ROLE_STUDENT
from services import school_service
from reports.report_card import generate_report_card_pdf


def render():
    user = require_role(ROLE_STUDENT)
    load_theme()
    page_header("My Results")

    db = get_session()
    try:
        profile = db.execute(select(StudentProfile).where(StudentProfile.user_id == user.id)).scalar_one_or_none()
    finally:
        db.close()

    if profile is None:
        empty_state("Your student profile could not be found.")
        return

    term = school_service.get_current_term()
    session = school_service.get_current_session()
    class_name = profile.current_class.name if profile.current_class else "Unassigned"

    if term is None:
        st.info("No academic term is currently active.")
        return

    pdf_bytes = generate_report_card_pdf(
        profile.admission_number, user.full_name, class_name, profile.id,
        term.name, session.name if session else "",
    )
    st.download_button(
        "Download Report Card (PDF)", data=pdf_bytes,
        file_name=f"report_card_{profile.admission_number}.pdf", mime="application/pdf",
    )
