import streamlit as st

from components.ui import page_header, load_theme
from services import auth_service


def render():
    load_theme()
    page_header("Create an Account", "Register as a parent or a teacher")

    role = st.radio("Register as", ["Parent", "Teacher"], horizontal=True)

    with st.form("register_form"):
        col1, col2 = st.columns(2)
        with col1:
            first_name = st.text_input("First Name")
        with col2:
            last_name = st.text_input("Last Name")
        email = st.text_input("Email")
        phone = st.text_input("Phone Number (optional)")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")

        class_id = None
        if role == "Teacher":
            classes = auth_service.get_active_classes_for_registration()
            options = {"None / not applying for a class teacher role": None}
            options.update({c["label"]: c["id"] for c in classes})
            chosen_label = st.selectbox("Class you are applying to teach (optional)", list(options.keys()))
            class_id = options[chosen_label]
            st.caption("Class assignment takes effect only after administrator approval.")

        submitted = st.form_submit_button("Register", type="primary")

    if submitted:
        if not all([first_name, last_name, email, password, confirm_password]):
            st.error("Please fill in all required fields.")
        elif password != confirm_password:
            st.error("Passwords do not match.")
        else:
            if role == "Parent":
                ok, message = auth_service.register_parent(first_name, last_name, email, password, phone)
            else:
                ok, message = auth_service.register_teacher(first_name, last_name, email, password, class_id, phone)

            if ok:
                st.success(message)
            else:
                st.error(message)

    st.divider()
    if st.button("Already have an account? Sign in"):
        st.session_state["nav_target"] = "login"
        st.rerun()
