import streamlit as st

from components.ui import page_header, load_theme, empty_state
from permissions.rbac import require_role, ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN
from services import audit_service


def render():
    require_role(ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN)
    load_theme()
    page_header("Audit Log")

    col1, col2, col3 = st.columns(3)
    with col1:
        user_email = st.text_input("Filter by user email")
    with col2:
        modules = ["All"] + audit_service.list_distinct_modules()
        module_choice = st.selectbox("Module", modules)
    with col3:
        action = st.text_input("Filter by action")

    col4, col5 = st.columns(2)
    with col4:
        start_date = st.date_input("From date", value=None)
    with col5:
        end_date = st.date_input("To date", value=None)

    entries = audit_service.search_audit_log(
        user_email=user_email,
        module=module_choice if module_choice != "All" else "",
        action=action,
        start_date=start_date if start_date else None,
        end_date=end_date if end_date else None,
    )

    if not entries:
        empty_state("No audit log entries match the current filters.")
        return

    st.table([{
        "Time": e.created_at.strftime("%Y-%m-%d %H:%M"),
        "User": e.user_email or "system",
        "Module": e.module,
        "Action": e.action,
        "Details": e.details or "",
    } for e in entries])
