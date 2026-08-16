from datetime import date

import streamlit as st
from sqlalchemy import select

from components.ui import page_header, load_theme, empty_state, metric_row
from database.connection import get_session
from models.people import TeacherProfile
from permissions.rbac import require_role, ROLE_TEACHER
from services import attendance_service


def render():
    user = require_role(ROLE_TEACHER)
    load_theme()
    page_header("Attendance", "Take and review attendance for your class")

    db = get_session()
    try:
        profile = db.execute(select(TeacherProfile).where(TeacherProfile.user_id == user.id)).scalar_one_or_none()
        classes = profile.classes_as_teacher if profile else []
    finally:
        db.close()

    if not classes:
        empty_state("You are not currently assigned as a class teacher for any class.")
        return

    class_options = {c.name: c.id for c in classes}
    class_label = st.selectbox("Class", list(class_options.keys()))
    class_id = class_options[class_label]

    selected_date = st.date_input("Date", value=date.today())

    roster = attendance_service.get_class_roster(class_id)
    existing = attendance_service.get_class_attendance_for_date(class_id, selected_date)

    if not roster:
        empty_state("No active students are currently in this class.")
        return

    is_locked = any(r.is_locked for r in existing.values())
    if is_locked:
        st.warning("Attendance for this date is locked.")

    summary = attendance_service.class_attendance_summary(class_id)
    metric_row([
        ("Students", str(len(roster))),
        ("Attendance Rate (all-time)", f"{summary['attendance_rate']}%"),
    ])

    statuses = {}
    with st.form("attendance_form"):
        for student in roster:
            current_status = existing[student.id].status if student.id in existing else "present"
            statuses[student.id] = st.selectbox(
                student.admission_number, ["present", "absent", "late", "excused"],
                index=["present", "absent", "late", "excused"].index(current_status),
                key=f"att_{student.id}_{selected_date}",
                disabled=is_locked,
            )
        col1, col2, col3 = st.columns(3)
        with col1:
            save_clicked = st.form_submit_button("Save Attendance", type="primary", disabled=is_locked)
        with col2:
            lock_clicked = st.form_submit_button("Lock Attendance", disabled=is_locked)
        with col3:
            reopen_clicked = st.form_submit_button("Reopen Attendance", disabled=not is_locked)

    if save_clicked:
        ok, message = attendance_service.save_attendance(class_id, selected_date, statuses, user.id)
        st.success(message) if ok else st.error(message)
        if ok:
            st.rerun()
    if lock_clicked:
        ok, message = attendance_service.lock_attendance(class_id, selected_date)
        st.success(message) if ok else st.error(message)
        st.rerun()
    if reopen_clicked:
        ok, message = attendance_service.reopen_attendance(class_id, selected_date)
        st.success(message) if ok else st.error(message)
        st.rerun()
