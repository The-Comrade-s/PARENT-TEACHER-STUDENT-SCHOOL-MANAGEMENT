import streamlit as st

from components.ui import page_header, load_theme
from auth.session import login as start_session
from services import auth_service


def render():
    load_theme()
    page_header("Sign In", "Parent-Teacher Communication and Student Monitoring System")

    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign In", type="primary")

    if submitted:
        if not email or not password:
            st.error("Please enter both email and password.")
        else:
            user, message = auth_service.authenticate(email, password)
            if user is not None:
                start_session(user)
                st.success("Signed in successfully.")
                st.rerun()
            else:
                st.error(message)

    st.divider()
    st.caption("Do not have an account?")
    if st.button("Create an account"):
        st.session_state["nav_target"] = "register"
        st.rerun()
