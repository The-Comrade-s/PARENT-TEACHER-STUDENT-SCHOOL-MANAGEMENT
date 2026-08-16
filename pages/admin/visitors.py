import streamlit as st

from components.ui import page_header, load_theme, empty_state
from permissions.rbac import require_role, ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN
from services import security_service


def render():
    user = require_role(ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN)
    load_theme()
    page_header("Visitors")

    with st.form("register_visitor_form"):
        col1, col2 = st.columns(2)
        with col1:
            full_name = st.text_input("Visitor Name")
            phone_number = st.text_input("Phone Number")
        with col2:
            purpose = st.text_input("Purpose of Visit")
            host_name = st.text_input("Host Name")
        if st.form_submit_button("Register and Check In", type="primary"):
            ok, message = security_service.register_visitor(full_name, phone_number, purpose, host_name, user.id)
            st.success(message) if ok else st.error(message)
            if ok:
                st.rerun()

    visitors = security_service.list_visitors()
    if not visitors:
        empty_state("No visitors recorded yet.")
        return

    for v in visitors:
        st.markdown('<div class="ptms-card">', unsafe_allow_html=True)
        st.write(f"{v.full_name} &middot; {v.purpose or 'No purpose given'}")
        st.caption(f"Host: {v.host_name or 'N/A'} &middot; Checked in: {v.checked_in_at}")
        if v.checked_out_at:
            st.caption(f"Checked out: {v.checked_out_at}")
        elif st.button("Check Out", key=f"checkout_visitor_{v.id}"):
            security_service.check_out_visitor(v.id)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
