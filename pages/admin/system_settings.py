import streamlit as st

from components.ui import page_header, load_theme
from permissions.rbac import require_role, ROLE_SUPER_ADMIN
from services import settings_service


def render():
    require_role(ROLE_SUPER_ADMIN)
    load_theme()
    page_header("System Settings", "Restricted to Super Administrators")

    settings_service.ensure_default_settings()

    st.subheader("System Health")
    health = settings_service.system_health_snapshot()
    st.write(
        f"Students: {health['students']} &middot; Teachers: {health['teachers']} &middot; "
        f"Parents: {health['parents']} &middot; Classes: {health['classes']}"
    )

    st.divider()
    st.subheader("Feature Flags & Policy")
    for setting in settings_service.list_all_settings():
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            st.write(setting.key.replace("_", " ").title())
        with col2:
            new_value = st.text_input("Value", value=setting.value or "", key=f"setting_{setting.id}", label_visibility="collapsed")
        with col3:
            if st.button("Save", key=f"save_setting_{setting.id}"):
                settings_service.set_setting(setting.key, new_value)
                st.rerun()
