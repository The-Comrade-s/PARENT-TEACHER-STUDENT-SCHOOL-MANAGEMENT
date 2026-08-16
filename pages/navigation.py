"""
Builds the Streamlit navigation menu for the authenticated user.

Only pages the user's role is allowed to see are included here -- but every
page function also calls require_role/require_permission itself (see
permissions/rbac.py), so this is a UX convenience, not the security boundary.
"""

import streamlit as st

from permissions.rbac import ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN, ROLE_TEACHER, ROLE_PARENT, ROLE_STUDENT


def build_navigation(role_names: list[str]) -> st.navigation:
    is_admin = ROLE_SUPER_ADMIN in role_names or ROLE_SCHOOL_ADMIN in role_names
    is_teacher = ROLE_TEACHER in role_names
    is_parent = ROLE_PARENT in role_names
    is_student = ROLE_STUDENT in role_names

    pages: dict[str, list[st.Page]] = {}
    from pages.notifications import render as notifications_render

    if is_admin:
        from pages.admin import (
            dashboard, school_setup, class_management, teacher_approvals,
            student_management, parent_management, teacher_management, results_publishing,
            announcements, messages, pta, security_dashboard, checkin_checkout, visitors,
            incidents, movements, emergency_alerts, audit_log, reports_exports, system_settings,
            global_search,
        )

        pages["Overview"] = [
            st.Page(dashboard.render, title="Dashboard", default=True),
            st.Page(global_search.render, title="Search"),
        ]
        pages["School Setup"] = [
            st.Page(school_setup.render, title="School Setup"),
            st.Page(class_management.render, title="Classes"),
        ]
        pages["People"] = [
            st.Page(teacher_approvals.render, title="Teacher Approvals"),
            st.Page(teacher_management.render, title="Teachers"),
            st.Page(student_management.render, title="Students"),
            st.Page(parent_management.render, title="Parents"),
        ]
        pages["Academics"] = [
            st.Page(results_publishing.render, title="Result Publishing"),
        ]
        pages["Communication"] = [
            st.Page(messages.render, title="Messages"),
            st.Page(announcements.render, title="Announcements"),
            st.Page(pta.render, title="PTA Meetings"),
            st.Page(notifications_render, title="Notifications"),
        ]
        pages["Security"] = [
            st.Page(security_dashboard.render, title="Security Dashboard"),
            st.Page(checkin_checkout.render, title="Check-In / Check-Out"),
            st.Page(visitors.render, title="Visitors"),
            st.Page(incidents.render, title="Incidents"),
            st.Page(movements.render, title="Student Movements"),
            st.Page(emergency_alerts.render, title="Emergency Alerts"),
        ]
        pages["System"] = [
            st.Page(audit_log.render, title="Audit Log"),
            st.Page(reports_exports.render, title="Reports & Exports"),
            st.Page(system_settings.render, title="System Settings"),
        ]

    elif is_teacher:
        from pages.teacher import dashboard, attendance, assignments, grading, behaviour, messages, meetings

        pages["Overview"] = [st.Page(dashboard.render, title="Dashboard", default=True)]
        pages["Classroom"] = [
            st.Page(attendance.render, title="Attendance"),
            st.Page(assignments.render, title="Assignments"),
            st.Page(grading.render, title="Grading"),
            st.Page(behaviour.render, title="Behaviour"),
        ]
        pages["Communication"] = [
            st.Page(messages.render, title="Messages"),
            st.Page(meetings.render, title="Meeting Requests"),
            st.Page(notifications_render, title="Notifications"),
        ]

    elif is_parent:
        from pages.parent import dashboard, child_results, behaviour, messages, meetings

        pages["Overview"] = [st.Page(dashboard.render, title="Dashboard", default=True)]
        pages["Academics"] = [
            st.Page(child_results.render, title="Children's Results"),
            st.Page(behaviour.render, title="Behaviour"),
        ]
        pages["Communication"] = [
            st.Page(messages.render, title="Messages"),
            st.Page(meetings.render, title="Meetings"),
            st.Page(notifications_render, title="Notifications"),
        ]

    elif is_student:
        from pages.student import dashboard, assignments, results

        pages["Overview"] = [st.Page(dashboard.render, title="Dashboard", default=True)]
        pages["Academics"] = [
            st.Page(assignments.render, title="Assignments"),
            st.Page(results.render, title="My Results"),
        ]
        pages["Communication"] = [
            st.Page(notifications_render, title="Notifications"),
        ]

    return st.navigation(pages)
