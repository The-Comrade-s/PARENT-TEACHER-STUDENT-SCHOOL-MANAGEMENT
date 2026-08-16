import streamlit as st

from components.ui import page_header, load_theme, metric_row
from permissions.rbac import require_role, ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN
from services import security_service


def render():
    require_role(ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN)
    load_theme()
    page_header("Security Dashboard")

    stats = security_service.security_dashboard_stats()
    metric_row([
        ("Total Check-Ins", str(stats["total_checkins"])),
        ("Open Incidents", str(stats["open_incidents"])),
        ("Visitors on Campus", str(stats["active_visitors"])),
        ("Active Emergency Alerts", str(stats["active_alerts"])),
    ])

    if stats["active_alerts"]:
        st.error(f"{stats['active_alerts']} active emergency alert(s). Check the Emergency Alerts page.")

    st.subheader("Recent Incidents")
    incidents = security_service.list_incidents(limit=5)
    if not incidents:
        st.caption("No incidents reported.")
    for i in incidents:
        st.markdown(
            f'<div class="ptms-card">{i.severity.title()} &middot; {i.status.title()}<br>{i.description}</div>',
            unsafe_allow_html=True,
        )
