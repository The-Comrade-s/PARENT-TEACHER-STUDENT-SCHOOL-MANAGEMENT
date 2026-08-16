"""
Builds the Streamlit navigation menu for the authenticated user.

Only pages the user's role is allowed to see are included here -- but every
page function also calls require_role/require_permission itself (see
permissions/rbac.py), so this is a UX convenience, not the security boundary.

IMPORTANT: every page module in this project defines its entry point as
`def render():` -- the same function name everywhere. st.Page() derives a
page's URL pathname from the callable's __name__ when url_path is not given
explicitly, so leaving url_path unset would make every single page collide
on the pathname "render". Every st.Page() call below must pass an explicit,
unique url_path for this reason.
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
    from pages.announcements import render as announcements_render

    if is_admin:
        from pages.admin import (
            dashboard, school_setup, class_management, teacher_approvals,
            student_management, parent_management, teacher_management, results_publishing,
            announcements, messages, pta, security_dashboard, checkin_checkout, visitors,
            incidents, movements, emergency_alerts, audit_log, reports_exports, system_settings,
            global_search,
        )

        pages["Overview"] = [
            st.Page(dashboard.render, title="Dashboard", url_path="admin-dashboard", default=True),
            st.Page(global_search.render, title="Search", url_path="admin-search"),
        ]
        pages["School Setup"] = [
            st.Page(school_setup.render, title="School Setup", url_path="school-setup"),
            st.Page(class_management.render, title="Classes", url_path="class-management"),
        ]
        pages["People"] = [
            st.Page(teacher_approvals.render, title="Teacher Approvals", url_path="teacher-approvals"),
            st.Page(teacher_management.render, title="Teachers", url_path="teacher-management"),
            st.Page(student_management.render, title="Students", url_path="student-management"),
            st.Page(parent_management.render, title="Parents", url_path="parent-management"),
        ]
        pages["Academics"] = [
            st.Page(results_publishing.render, title="Result Publishing", url_path="result-publishing"),
        ]
        pages["Communication"] = [
            st.Page(messages.render, title="Messages", url_path="admin-messages"),
            st.Page(announcements.render, title="Announcements", url_path="announcements"),
            st.Page(pta.render, title="PTA Meetings", url_path="pta-meetings"),
            st.Page(notifications_render, title="Notifications", url_path="admin-notifications"),
        ]
        pages["Security"] = [
            st.Page(security_dashboard.render, title="Security Dashboard", url_path="security-dashboard"),
            st.Page(checkin_checkout.render, title="Check-In / Check-Out", url_path="checkin-checkout"),
            st.Page(visitors.render, title="Visitors", url_path="visitors"),
            st.Page(incidents.render, title="Incidents", url_path="incidents"),
            st.Page(movements.render, title="Student Movements", url_path="student-movements"),
            st.Page(emergency_alerts.render, title="Emergency Alerts", url_path="emergency-alerts"),
        ]
        pages["System"] = [
            st.Page(audit_log.render, title="Audit Log", url_path="audit-log"),
            st.Page(reports_exports.render, title="Reports & Exports", url_path="reports-exports"),
            st.Page(system_settings.render, title="System Settings", url_path="system-settings"),
        ]

    elif is_teacher:
        from pages.teacher import dashboard, attendance, assignments, grading, behaviour, messages, meetings

        pages["Overview"] = [
            st.Page(dashboard.render, title="Dashboard", url_path="teacher-dashboard", default=True),
        ]
        pages["Classroom"] = [
            st.Page(attendance.render, title="Attendance", url_path="teacher-attendance"),
            st.Page(assignments.render, title="Assignments", url_path="teacher-assignments"),
            st.Page(grading.render, title="Grading", url_path="teacher-grading"),
            st.Page(behaviour.render, title="Behaviour", url_path="teacher-behaviour"),
        ]
        pages["Communication"] = [
            st.Page(messages.render, title="Messages", url_path="teacher-messages"),
            st.Page(meetings.render, title="Meeting Requests", url_path="teacher-meetings"),
            st.Page(announcements_render, title="Announcements", url_path="teacher-announcements"),
            st.Page(notifications_render, title="Notifications", url_path="teacher-notifications"),
        ]

    elif is_parent:
        from pages.parent import dashboard, child_results, behaviour, messages, meetings

        pages["Overview"] = [
            st.Page(dashboard.render, title="Dashboard", url_path="parent-dashboard", default=True),
        ]
        pages["Academics"] = [
            st.Page(child_results.render, title="Children's Results", url_path="child-results"),
            st.Page(behaviour.render, title="Behaviour", url_path="parent-behaviour"),
        ]
        pages["Communication"] = [
            st.Page(messages.render, title="Messages", url_path="parent-messages"),
            st.Page(meetings.render, title="Meetings", url_path="parent-meetings"),
            st.Page(announcements_render, title="Announcements", url_path="parent-announcements"),
            st.Page(notifications_render, title="Notifications", url_path="parent-notifications"),
        ]

    elif is_student:
        from pages.student import dashboard, assignments, results

        pages["Overview"] = [
            st.Page(dashboard.render, title="Dashboard", url_path="student-dashboard", default=True),
        ]
        pages["Academics"] = [
            st.Page(assignments.render, title="Assignments", url_path="student-assignments"),
            st.Page(results.render, title="My Results", url_path="student-results"),
        ]
        pages["Communication"] = [
            st.Page(announcements_render, title="Announcements", url_path="student-announcements"),
            st.Page(notifications_render, title="Notifications", url_path="student-notifications"),
        ]

    return st.navigation(pages)
