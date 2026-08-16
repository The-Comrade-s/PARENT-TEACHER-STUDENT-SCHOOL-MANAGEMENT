import streamlit as st

from components.ui import page_header, load_theme, empty_state
from permissions.rbac import require_role, ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN, ALL_ROLES, ROLE_DISPLAY_NAMES
from services import notification_service


def render():
    user = require_role(ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN)
    load_theme()
    page_header("Announcements")

    with st.form("new_announcement_form"):
        title = st.text_input("Title")
        body = st.text_area("Message")
        target_label = st.selectbox("Audience", ["Everyone"] + [ROLE_DISPLAY_NAMES[r] for r in ALL_ROLES])
        target_role = None
        if target_label != "Everyone":
            for role_name, display in ROLE_DISPLAY_NAMES.items():
                if display == target_label:
                    target_role = role_name
        if st.form_submit_button("Publish Announcement", type="primary"):
            ok, message = notification_service.create_announcement(user.id, title, body, target_role)
            st.success(message) if ok else st.error(message)
            if ok:
                st.rerun()

    st.divider()
    announcements = notification_service.list_announcements()
    if not announcements:
        empty_state("No announcements published yet.")
        return
    for a in announcements:
        audience = a.target_role.replace('_', ' ').title() if a.target_role else "Everyone"
        st.markdown(
            f'<div class="ptms-card"><strong>{a.title}</strong> &middot; {audience}<br>{a.body}<br>'
            f'<small>{a.created_at.strftime("%Y-%m-%d %H:%M")}</small></div>',
            unsafe_allow_html=True,
        )
