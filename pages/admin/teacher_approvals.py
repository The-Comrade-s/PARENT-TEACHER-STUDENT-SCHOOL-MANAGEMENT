import streamlit as st

from components.ui import page_header, load_theme, empty_state
from permissions.rbac import require_role, ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN
from services import teacher_service, school_service


def render():
    user = require_role(ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN)
    load_theme()
    page_header("Teacher Approvals", "Review pending teacher registrations")

    pending = teacher_service.list_pending_teachers()
    if not pending:
        empty_state("No teacher accounts are awaiting approval.")
        return

    active_classes = school_service.list_active_classes()
    class_options = {"Do not assign a class": None}
    class_options.update({c.name: c.id for c in active_classes})

    for teacher in pending:
        with st.container():
            st.markdown('<div class="ptms-card">', unsafe_allow_html=True)
            st.markdown(f"**{teacher['name']}** &middot; {teacher['email']}", unsafe_allow_html=True)
            if teacher["requested_class_name"]:
                st.caption(f"Requested class at registration: {teacher['requested_class_name']}")
            else:
                st.caption("No class was requested at registration.")

            default_label = None
            for label, cid in class_options.items():
                if cid == teacher["requested_class_id"]:
                    default_label = label
            default_index = list(class_options.keys()).index(default_label) if default_label else 0

            chosen_label = st.selectbox(
                "Assign class on approval",
                list(class_options.keys()),
                index=default_index,
                key=f"class_select_{teacher['teacher_profile_id']}",
            )
            chosen_class_id = class_options[chosen_label]

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Approve", key=f"approve_{teacher['teacher_profile_id']}", type="primary"):
                    if chosen_class_id and chosen_class_id != teacher["requested_class_id"]:
                        # Admin picked a different class than requested; save it before approving.
                        db_ok, _ = teacher_service.assign_class_teacher(
                            teacher["teacher_profile_id"], chosen_class_id, actor_user_id=user.id
                        )
                    ok, message = teacher_service.approve_teacher(
                        teacher["teacher_profile_id"], user.id, assign_requested_class=bool(chosen_class_id)
                    )
                    if ok:
                        st.success(message)
                    else:
                        st.error(message)
                    st.rerun()
            with col2:
                if st.button("Reject", key=f"reject_{teacher['teacher_profile_id']}"):
                    ok, message = teacher_service.reject_teacher(teacher["teacher_profile_id"], user.id)
                    if ok:
                        st.success(message)
                    else:
                        st.error(message)
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
