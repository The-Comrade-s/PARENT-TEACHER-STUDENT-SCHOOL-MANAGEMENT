"""Shared conversation UI, used by teacher/parent/admin messaging pages."""

import streamlit as st
from sqlalchemy import select

from database.connection import get_session
from models.user import User
from services import messaging_service


def render_messaging(current_user_id: str, contact_choices: dict[str, str]):
    """contact_choices: {display_name: user_id} of people this user is allowed to message."""
    col_list, col_thread = st.columns([1, 2])

    with col_list:
        st.subheader("Conversations")
        conversations = messaging_service.list_conversations_for_user(current_user_id)
        selected_conv_id = st.session_state.get("active_conversation_id")

        if contact_choices:
            with st.expander("Start a new conversation"):
                contact_label = st.selectbox("Contact", list(contact_choices.keys()), key="new_conv_contact")
                if st.button("Start Conversation"):
                    conv_id = messaging_service.get_or_create_conversation(
                        current_user_id, contact_choices[contact_label]
                    )
                    st.session_state["active_conversation_id"] = conv_id
                    st.rerun()

        for c in conversations:
            label = f"{c['with']}"
            if st.button(label, key=f"conv_btn_{c['id']}", use_container_width=True):
                st.session_state["active_conversation_id"] = c["id"]
                st.rerun()

        search_query = st.text_input("Search messages", key="msg_search")
        if search_query:
            matches = messaging_service.search_messages(current_user_id, search_query)
            for m in matches:
                st.caption(m["body"][:80])

    with col_thread:
        active_id = st.session_state.get("active_conversation_id")
        if not active_id:
            st.info("Select or start a conversation.")
            return

        st.subheader("Messages")
        messages = messaging_service.list_messages(active_id)
        db = get_session()
        try:
            for m in messages:
                sender = db.get(User, m.sender_id)
                sender_name = sender.full_name if sender else "Unknown"
                align = "You" if m.sender_id == current_user_id else sender_name
                st.markdown(f"**{align}:** {m.body}")
        finally:
            db.close()

        with st.form("send_message_form", clear_on_submit=True):
            body = st.text_area("Message", label_visibility="collapsed", placeholder="Type a message...")
            col1, col2 = st.columns(2)
            with col1:
                send_clicked = st.form_submit_button("Send", type="primary")
            with col2:
                archive_clicked = st.form_submit_button("Archive Conversation")

        if send_clicked and body:
            messaging_service.send_message(active_id, current_user_id, body)
            st.rerun()
        if archive_clicked:
            messaging_service.archive_conversation(active_id)
            st.session_state["active_conversation_id"] = None
            st.rerun()
