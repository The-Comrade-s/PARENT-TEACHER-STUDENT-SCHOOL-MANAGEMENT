import streamlit as st

from components.ui import page_header, load_theme, empty_state
from permissions.rbac import require_role, ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN
from services import people_service, school_service


def render():
    require_role(ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN)
    load_theme()
    page_header("Teacher Management")

    search = st.text_input("Search teachers by name or email")
    teachers = people_service.list_teachers(search=search)

    if not teachers:
        empty_state("No teachers found.")
        return

    departments = school_service.list_departments()
    dept_options = {"None": None}
    dept_options.update({d.name: d.id for d in departments})

    for t in teachers:
        st.markdown('<div class="ptms-card">', unsafe_allow_html=True)
        st.markdown(f"**{t['name']}** &middot; {t['email']} &middot; {t['approval_status'].title()}")
        st.caption(f"Class: {t['assigned_class_name'] or 'Unassigned'} &middot; Employment: {t['employment_status']}")

        with st.form(f"edit_teacher_{t['id']}"):
            col1, col2, col3 = st.columns(3)
            with col1:
                employee_id = st.text_input("Employee ID", value=t["employee_id"] or "", key=f"emp_{t['id']}")
            with col2:
                dept_label = st.selectbox("Department", list(dept_options.keys()), key=f"dept_{t['id']}")
            with col3:
                employment_status = st.selectbox(
                    "Employment Status", ["active", "on_leave", "terminated"],
                    index=["active", "on_leave", "terminated"].index(t["employment_status"]),
                    key=f"status_{t['id']}",
                )
            qualification = st.text_input("Qualification", key=f"qual_{t['id']}")
            if st.form_submit_button("Save"):
                ok, message = people_service.update_teacher_profile(
                    t["id"], employee_id=employee_id, qualification=qualification,
                    department_id=dept_options[dept_label], employment_status=employment_status,
                )
                st.success(message) if ok else st.error(message)
        st.markdown('</div>', unsafe_allow_html=True)
