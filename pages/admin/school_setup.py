import streamlit as st

from components.ui import page_header, load_theme
from permissions.rbac import require_role, ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN
from services import school_service


def render():
    require_role(ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN)
    load_theme()
    page_header("School Setup", "Profile, sessions, terms, departments, and subjects")

    tabs = st.tabs(["School Profile", "Sessions & Terms", "Departments", "Subjects"])

    with tabs[0]:
        profile = school_service.get_school_profile()
        with st.form("school_profile_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("School Name", value=profile.name if profile else "")
                motto = st.text_input("Motto", value=profile.motto if profile else "")
                email = st.text_input("Email", value=profile.email if profile else "")
                phone = st.text_input("Phone", value=profile.phone if profile else "")
                website = st.text_input("Website", value=profile.website if profile else "")
                principal_name = st.text_input("Principal Name", value=profile.principal_name if profile else "")
            with col2:
                address = st.text_input("Address", value=profile.address if profile else "")
                city = st.text_input("City", value=profile.city if profile else "")
                state = st.text_input("State", value=profile.state if profile else "")
                country = st.text_input("Country", value=profile.country if profile else "")
                school_type = st.text_input("School Type", value=profile.school_type if profile else "")
                school_level = st.text_input("School Level", value=profile.school_level if profile else "")
            if st.form_submit_button("Save Profile", type="primary"):
                ok, message = school_service.save_school_profile({
                    "name": name, "motto": motto, "email": email, "phone": phone, "website": website,
                    "principal_name": principal_name, "address": address, "city": city, "state": state,
                    "country": country, "school_type": school_type, "school_level": school_level,
                })
                st.success(message) if ok else st.error(message)

    with tabs[1]:
        st.subheader("Academic Sessions")
        with st.form("new_session_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                s_name = st.text_input("Session Name (e.g. 2025/2026)")
            with col2:
                s_start = st.text_input("Start Date")
            with col3:
                s_end = st.text_input("End Date")
            if st.form_submit_button("Create Session"):
                ok, message = school_service.create_session(s_name, s_start, s_end)
                st.success(message) if ok else st.error(message)
                if ok:
                    st.rerun()

        for s in school_service.list_sessions():
            col1, col2 = st.columns([4, 1])
            with col1:
                marker = " (current)" if s.is_current else ""
                st.write(f"{s.name}{marker}")
            with col2:
                if not s.is_current and st.button("Activate", key=f"activate_session_{s.id}"):
                    school_service.activate_session(s.id)
                    st.rerun()

        st.divider()
        st.subheader("Academic Terms")
        sessions = school_service.list_sessions()
        if sessions:
            session_options = {s.name: s.id for s in sessions}
            with st.form("new_term_form"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    session_label = st.selectbox("Session", list(session_options.keys()))
                with col2:
                    t_name = st.text_input("Term Name (e.g. First Term)")
                with col3:
                    t_start = st.text_input("Term Start Date")
                if st.form_submit_button("Create Term"):
                    ok, message = school_service.create_term(session_options[session_label], t_name, t_start)
                    st.success(message) if ok else st.error(message)
                    if ok:
                        st.rerun()

            for t in school_service.list_terms():
                col1, col2 = st.columns([4, 1])
                with col1:
                    marker = " (current)" if t.is_current else ""
                    st.write(f"{t.name}{marker}")
                with col2:
                    if not t.is_current and st.button("Activate", key=f"activate_term_{t.id}"):
                        school_service.activate_term(t.id)
                        st.rerun()
        else:
            st.caption("Create an academic session first.")

    with tabs[2]:
        st.subheader("Departments")
        with st.form("new_department_form"):
            d_name = st.text_input("Department Name")
            d_desc = st.text_area("Description")
            if st.form_submit_button("Create Department"):
                ok, message = school_service.create_department(d_name, d_desc)
                st.success(message) if ok else st.error(message)
                if ok:
                    st.rerun()
        for d in school_service.list_departments():
            st.markdown(f'<div class="ptms-card"><strong>{d.name}</strong><br>{d.description or ""}</div>', unsafe_allow_html=True)

    with tabs[3]:
        st.subheader("Subjects")
        departments = school_service.list_departments()
        dept_options = {"None": None}
        dept_options.update({d.name: d.id for d in departments})
        with st.form("new_subject_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                sub_name = st.text_input("Subject Name")
            with col2:
                sub_code = st.text_input("Subject Code")
            with col3:
                dept_label = st.selectbox("Department", list(dept_options.keys()))
            if st.form_submit_button("Create Subject"):
                ok, message = school_service.create_subject(sub_name, sub_code, dept_options[dept_label])
                st.success(message) if ok else st.error(message)
                if ok:
                    st.rerun()
        for sub in school_service.list_subjects():
            st.markdown(f'<div class="ptms-card"><strong>{sub.name}</strong> ({sub.code})</div>', unsafe_allow_html=True)
