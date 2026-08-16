import streamlit as st

from components.ui import page_header, load_theme, empty_state
from permissions.rbac import require_role, ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN
from services import people_service, school_service


def render():
    require_role(ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN)
    load_theme()
    page_header("Student Management")

    with st.expander("Register a new student"):
        classes = school_service.list_active_classes()
        class_options = {"Unassigned": None}
        class_options.update({c.name: c.id for c in classes})

        with st.form("new_student_form"):
            col1, col2 = st.columns(2)
            with col1:
                first_name = st.text_input("First Name")
                last_name = st.text_input("Last Name")
                admission_number = st.text_input("Admission Number")
            with col2:
                class_label = st.selectbox("Class", list(class_options.keys()))
                emergency_name = st.text_input("Emergency Contact Name")
                emergency_phone = st.text_input("Emergency Contact Phone")

            create_login = st.checkbox("Create a login for this student")
            email, password = "", ""
            if create_login:
                email = st.text_input("Student Email")
                password = st.text_input("Temporary Password", type="password")

            if st.form_submit_button("Register Student", type="primary"):
                ok, message = people_service.create_student(
                    first_name, last_name, admission_number, class_options[class_label],
                    emergency_name=emergency_name, emergency_phone=emergency_phone,
                    create_login=create_login, email=email, password=password,
                )
                st.success(message) if ok else st.error(message)
                if ok:
                    st.rerun()

    search = st.text_input("Search students by name or admission number")
    students = people_service.list_students(search=search)

    if not students:
        empty_state("No students found.")
        return

    classes = school_service.list_active_classes()
    class_options = {"Unassigned": None}
    class_options.update({c.name: c.id for c in classes})

    for s in students:
        st.markdown('<div class="ptms-card">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            st.markdown(f"**{s['name']}** &middot; {s['admission_number']}")
            st.caption(f"Class: {s['class_name']} &middot; Status: {s['status']}")
        with col2:
            new_class_label = st.selectbox(
                "Reassign class", list(class_options.keys()),
                index=list(class_options.keys()).index(s["class_name"]) if s["class_name"] in class_options else 0,
                key=f"class_reassign_{s['id']}",
            )
        with col3:
            if st.button("Save", key=f"save_student_class_{s['id']}"):
                people_service.update_student_class(s["id"], class_options[new_class_label])
                st.rerun()
            toggle_label = "Deactivate" if s["status"] == "active" else "Activate"
            if st.button(toggle_label, key=f"toggle_student_{s['id']}"):
                people_service.set_student_status(s["id"], "inactive" if s["status"] == "active" else "active")
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
