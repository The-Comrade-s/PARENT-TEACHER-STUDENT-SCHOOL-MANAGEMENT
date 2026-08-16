import streamlit as st
from sqlalchemy import select, func

from components.ui import page_header, metric_row, load_theme, empty_state
from database.connection import get_session
from models.people import StudentProfile, ParentProfile, TeacherProfile
from models.school import SchoolClass
from models.user import AuditLog
from permissions.rbac import require_role, ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN


def render():
    user = require_role(ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN)
    load_theme()
    page_header("Administrator Dashboard", f"Welcome, {user.full_name}")

    db = get_session()
    try:
        total_students = db.execute(select(func.count(StudentProfile.id))).scalar_one()
        total_parents = db.execute(select(func.count(ParentProfile.id))).scalar_one()
        total_teachers = db.execute(select(func.count(TeacherProfile.id))).scalar_one()
        total_classes = db.execute(select(func.count(SchoolClass.id))).scalar_one()
        pending_teachers = db.execute(
            select(func.count(TeacherProfile.id)).where(TeacherProfile.approval_status == "pending")
        ).scalar_one()
        recent_activity = db.execute(
            select(AuditLog).order_by(AuditLog.created_at.desc()).limit(10)
        ).scalars().all()
    finally:
        db.close()

    metric_row([
        ("Students", str(total_students)),
        ("Parents", str(total_parents)),
        ("Teachers", str(total_teachers)),
        ("Classes", str(total_classes)),
    ])

    if pending_teachers:
        st.warning(f"{pending_teachers} teacher account(s) awaiting approval.")

    st.subheader("Recent Activity")
    if recent_activity:
        for entry in recent_activity:
            st.markdown(
                f'<div class="ptms-card"><strong>{entry.action}</strong> &middot; {entry.module} '
                f'&middot; {entry.user_email or "system"} &middot; '
                f'{entry.created_at.strftime("%Y-%m-%d %H:%M")}</div>',
                unsafe_allow_html=True,
            )
    else:
        empty_state("No recent activity recorded yet.")

    st.info(
        "Attendance, academic, behaviour, assignment, and security overviews are added in later phases "
        "(PTMS-003 through PTMS-005)."
    )
