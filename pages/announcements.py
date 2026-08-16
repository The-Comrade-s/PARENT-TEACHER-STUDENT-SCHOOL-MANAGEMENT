import streamlit as st

from components.ui import page_header, load_theme, empty_state
from auth.session import require_login
from services import notification_service


def render():
    user = require_login()
    load_theme()
    page_header("Announcements")

    role_names = [r.name for r in user.roles]
    announcements = [
        a for a in notification_service.list_announcements()
        if a.target_role is None or a.target_role in role_names
    ]

    if not announcements:
        empty_state("No announcements have been published yet.")
        return

    for a in announcements:
        st.markdown(
            f'<div class="ptms-card"><strong>{a.title}</strong><br>{a.body}<br>'
            f'<small>{a.created_at.strftime("%Y-%m-%d %H:%M")}</small></div>',
            unsafe_allow_html=True,
        )
