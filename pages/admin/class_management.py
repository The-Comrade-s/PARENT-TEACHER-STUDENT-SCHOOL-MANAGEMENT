import streamlit as st

from components.ui import page_header, load_theme
from permissions.rbac import require_role, ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN
from services import school_service, teacher_service, people_service


def render():
    user = require_role(ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN)
    load_theme()
    page_header("Class Management", "Create classes and assign class teachers")

    with st.expander("Create a new class"):
        with st.form("new_class_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                c_name = st.text_input("Class Name (e.g. JSS 1A)")
            with col2:
                c_level = st.text_input("Level (e.g. JSS1)")
            with col3:
                c_capacity = st.number_input("Capacity", min_value=1, value=40)
            if st.form_submit_button("Create Class", type="primary"):
                ok, message = school_service.create_class(c_name, c_level, int(c_capacity))
                st.success(message) if ok else st.error(message)
                if ok:
                    st.rerun()

    approved_teachers = [t for t in people_service.list_teachers(approval_status="approved")]
    teacher_options = {"Unassigned": None}
    teacher_options.update({t["name"]: t["id"] for t in approved_teachers})

    classes = school_service.list_all_classes()
    if not classes:
        st.info("No classes have been created yet.")
        return

    for c in classes:
        st.markdown('<div class="ptms-card">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            status = "Active" if c.is_active else "Inactive"
            st.markdown(f"**{c.name}** &middot; {c.level or 'No level set'} &middot; {status}")
            current_teacher_name = "Unassigned"
            for t in approved_teachers:
                if t["assigned_class_name"] == c.name:
                    current_teacher_name = t["name"]
            st.caption(f"Class teacher: {current_teacher_name}")
        with col2:
            default_label = next((label for label, tid in teacher_options.items() if label == current_teacher_name), "Unassigned")
            default_index = list(teacher_options.keys()).index(default_label) if default_label in teacher_options else 0
            chosen_label = st.selectbox(
                "Class teacher", list(teacher_options.keys()), index=default_index, key=f"teacher_select_{c.id}"
            )
        with col3:
            if st.button("Update", key=f"update_class_teacher_{c.id}"):
                chosen_id = teacher_options[chosen_label]
                if chosen_id is None:
                    ok, message = teacher_service.remove_class_teacher(c.id, actor_user_id=user.id)
                else:
                    ok, message = teacher_service.assign_class_teacher(chosen_id, c.id, actor_user_id=user.id)
                st.success(message) if ok else st.error(message)
                st.rerun()
            toggle_label = "Deactivate" if c.is_active else "Activate"
            if st.button(toggle_label, key=f"toggle_class_{c.id}"):
                school_service.set_class_active(c.id, not c.is_active)
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
