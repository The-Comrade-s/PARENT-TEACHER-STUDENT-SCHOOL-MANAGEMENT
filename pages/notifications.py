import streamlit as st

from components.ui import page_header, load_theme, empty_state
from auth.session import require_login
from services import notification_service


def render():
    user = require_login()
    load_theme()
    page_header("Notifications")

    notifications = notification_service.list_notifications(user.id)
    if not notifications:
        empty_state("You have no notifications yet.")
        return

    if st.button("Mark all as read"):
        notification_service.mark_all_read(user.id)
        st.rerun()

    for n in notifications:
        read_marker = "" if n.is_read else " (new)"
        with st.container():
            st.markdown(
                f'<div class="ptms-card"><strong>{n.title}{read_marker}</strong><br>{n.body or ""}<br>'
                f'<small>{n.created_at.strftime("%Y-%m-%d %H:%M")}</small></div>',
                unsafe_allow_html=True,
            )
            if not n.is_read and st.button("Mark as read", key=f"read_{n.id}"):
                notification_service.mark_notification_read(n.id)
                st.rerun()
