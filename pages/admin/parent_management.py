import streamlit as st

from components.ui import page_header, load_theme, empty_state
from database.connection import get_session
from models.people import ParentProfile
from permissions.rbac import require_role, ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN
from services import people_service


def render():
    require_role(ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN)
    load_theme()
    page_header("Parent Management", "Link parents to their children")

    search = st.text_input("Search parents by name or email")
    parents = people_service.list_parents(search=search)

    if not parents:
        empty_state("No parents found.")
        return

    students = people_service.list_students_for_linking()
    student_options = {s["label"]: s["id"] for s in students}

    for p in parents:
        st.markdown('<div class="ptms-card">', unsafe_allow_html=True)
        st.markdown(f"**{p['name']}** &middot; {p['email']} &middot; {p['children_count']} linked child(ren)")

        col1, col2 = st.columns([3, 1])
        with col1:
            if student_options:
                chosen_label = st.selectbox(
                    "Link a child by admission number", list(student_options.keys()), key=f"link_select_{p['id']}"
                )
            else:
                chosen_label = None
                st.caption("No students available to link yet.")
        with col2:
            if chosen_label and st.button("Link Child", key=f"link_btn_{p['id']}"):
                ok, message = people_service.link_parent_to_student(p["id"], student_options[chosen_label])
                st.success(message) if ok else st.error(message)
                st.rerun()

        db = get_session()
        try:
            profile = db.get(ParentProfile, p["id"])
            links = profile.children_links if profile else []
            for link in links:
                student = link.student
                cols = st.columns([3, 1])
                with cols[0]:
                    label = student.admission_number if student else "Unknown"
                    st.caption(f"Linked: {label}")
                with cols[1]:
                    if st.button("Unlink", key=f"unlink_{link.id}"):
                        people_service.unlink_parent_from_student(link.id)
                        st.rerun()
        finally:
            db.close()

        st.markdown('</div>', unsafe_allow_html=True)
