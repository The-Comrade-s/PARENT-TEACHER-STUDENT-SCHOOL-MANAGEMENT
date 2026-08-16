"""
Parent-Teacher Communication and Student Monitoring System (PTMS)
Main application entrypoint.

Navigation shows only the pages a user is authorized to see, and every
page also re-verifies authorization itself (see permissions/rbac.py),
so hiding a link is never the only line of defense.
"""

import streamlit as st

from auth.session import get_current_user, logout
from config.settings import settings
from database.connection import init_database
from services.auth_service import seed_roles_and_admin
from services.results_service import ensure_default_grading_setup
from services.settings_service import ensure_default_settings
from utils.error_handling import log_technical_error

st.set_page_config(
    page_title=settings.app_short_name,
    layout="wide",
    initial_sidebar_state="expanded",
)

try:
    init_database()
    seed_roles_and_admin()
    ensure_default_grading_setup()
    ensure_default_settings()
except Exception as exc:  # noqa: BLE001 - top-level startup safety net
    log_technical_error("app.startup", exc)
    st.error("The application could not start due to a configuration or database issue. Contact an administrator.")
    st.stop()

user = get_current_user()

if user is None:
    from pages import login, register

    tab_login, tab_register = st.tabs(["Sign In", "Register"])
    with tab_login:
        login.render()
    with tab_register:
        register.render()

else:
    role_names = [r.name for r in user.roles]

    with st.sidebar:
        st.markdown(f"### {settings.app_short_name}")
        st.caption(settings.app_name)
        st.divider()
        st.markdown(f"**{user.full_name}**")
        st.caption(", ".join(r.replace('_', ' ').title() for r in role_names) or "No role assigned")
        st.divider()
        if st.button("Sign Out", use_container_width=True):
            logout()
            st.rerun()

    if not role_names:
        st.error("Your account has no assigned role. Contact an administrator.")
    else:
        from pages.navigation import build_navigation

        nav = build_navigation(role_names)
        nav.run()
