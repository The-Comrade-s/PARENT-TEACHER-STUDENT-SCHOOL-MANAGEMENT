import streamlit as st

from components.ui import page_header, load_theme, empty_state
from permissions.rbac import require_role, ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN
from services import security_service


def render():
    user = require_role(ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN)
    load_theme()
    page_header("Emergency Alerts", "Restricted to authorized personnel")

    with st.form("new_alert_form"):
        alert_type = st.selectbox("Alert Type", ["fire", "lockdown", "medical", "weather", "other"])
        message = st.text_area("Alert Message")
        if st.form_submit_button("Issue Emergency Alert", type="primary"):
            ok, msg = security_service.create_emergency_alert(user.id, alert_type, message)
            st.success(msg) if ok else st.error(msg)
            if ok:
                st.rerun()

    alerts = security_service.list_alerts()
    if not alerts:
        empty_state("No emergency alerts recorded.")
        return

    for a in alerts:
        st.markdown('<div class="ptms-card">', unsafe_allow_html=True)
        st.write(f"{a.alert_type.title()} &middot; {a.alert_status.title()}")
        st.write(a.message)
        if a.alert_status == "active" and st.button("Clear Alert", key=f"clear_{a.id}"):
            security_service.clear_alert(a.id)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
