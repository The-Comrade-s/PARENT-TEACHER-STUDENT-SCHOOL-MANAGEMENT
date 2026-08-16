"""Internal messaging between parents, teachers, and administrators."""

from sqlalchemy import select

from database.connection import get_session
from models.communication import Conversation, ConversationParticipant, Message
from models.user import User


def get_or_create_conversation(user_id_a: str, user_id_b: str, subject: str = "") -> str:
    """Finds an existing 1:1 conversation between two users, or creates one."""
    db = get_session()
    try:
        a_conv_ids = {
            p.conversation_id for p in db.execute(
                select(ConversationParticipant).where(ConversationParticipant.user_id == user_id_a)
            ).scalars().all()
        }
        b_conv_ids = {
            p.conversation_id for p in db.execute(
                select(ConversationParticipant).where(ConversationParticipant.user_id == user_id_b)
            ).scalars().all()
        }
        shared = a_conv_ids & b_conv_ids
        if shared:
            return next(iter(shared))

        conversation = Conversation(subject=subject or None)
        db.add(conversation)
        db.flush()
        db.add(ConversationParticipant(conversation_id=conversation.id, user_id=user_id_a))
        db.add(ConversationParticipant(conversation_id=conversation.id, user_id=user_id_b))
        db.commit()
        return conversation.id
    finally:
        db.close()


def list_conversations_for_user(user_id: str) -> list[dict]:
    db = get_session()
    try:
        participant_rows = db.execute(
            select(ConversationParticipant).where(ConversationParticipant.user_id == user_id)
        ).scalars().all()

        results = []
        for p in participant_rows:
            conversation = db.get(Conversation, p.conversation_id)
            if conversation is None or conversation.is_archived:
                continue
            others = db.execute(
                select(ConversationParticipant).where(
                    ConversationParticipant.conversation_id == conversation.id,
                    ConversationParticipant.user_id != user_id,
                )
            ).scalars().all()
            other_names = []
            for o in others:
                other_user = db.get(User, o.user_id)
                if other_user:
                    other_names.append(other_user.full_name)
            last_message = db.execute(
                select(Message)
                .where(Message.conversation_id == conversation.id)
                .order_by(Message.created_at.desc())
                .limit(1)
            ).scalar_one_or_none()
            results.append({
                "id": conversation.id,
                "with": ", ".join(other_names) or "Unknown",
                "last_message": last_message.body if last_message else "",
                "last_message_at": last_message.created_at if last_message else conversation.created_at,
            })
        results.sort(key=lambda r: r["last_message_at"], reverse=True)
        return results
    finally:
        db.close()


def list_messages(conversation_id: str) -> list[Message]:
    db = get_session()
    try:
        return list(db.execute(
            select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at)
        ).scalars().all())
    finally:
        db.close()


def send_message(conversation_id: str, sender_id: str, body: str) -> tuple[bool, str]:
    if not body.strip():
        return False, "Message cannot be empty."
    db = get_session()
    try:
        db.add(Message(conversation_id=conversation_id, sender_id=sender_id, body=body.strip()))
        db.commit()
        return True, "Message sent."
    finally:
        db.close()


def archive_conversation(conversation_id: str) -> tuple[bool, str]:
    db = get_session()
    try:
        conversation = db.get(Conversation, conversation_id)
        if conversation is None:
            return False, "Conversation not found."
        conversation.is_archived = True
        db.commit()
        return True, "Conversation archived."
    finally:
        db.close()


def search_messages(user_id: str, query: str) -> list[dict]:
    db = get_session()
    try:
        conv_ids = {
            p.conversation_id for p in db.execute(
                select(ConversationParticipant).where(ConversationParticipant.user_id == user_id)
            ).scalars().all()
        }
        if not conv_ids or not query.strip():
            return []
        matches = db.execute(
            select(Message).where(
                Message.conversation_id.in_(conv_ids), Message.body.ilike(f"%{query.strip()}%")
            )
        ).scalars().all()
        return [{"conversation_id": m.conversation_id, "body": m.body, "created_at": m.created_at} for m in matches]
    finally:
        db.close()
