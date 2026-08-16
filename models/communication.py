"""Behaviour records, messaging, notifications, announcements, and meetings."""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from models.base import BaseModel


class BehaviourRecord(BaseModel):
    __tablename__ = "behaviour_records"

    student_id = Column(String(36), ForeignKey("student_profiles.id"), nullable=False)
    recorded_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    category = Column(String(20), nullable=False)          # positive, negative
    description = Column(Text, nullable=False)
    disciplinary_action = Column(String(300), nullable=True)
    action_status = Column(String(20), default="open", nullable=False)  # open, resolved
    parent_notified = Column(Boolean, default=False, nullable=False)

    student = relationship("StudentProfile")


class Conversation(BaseModel):
    __tablename__ = "conversations"

    subject = Column(String(255), nullable=True)
    is_archived = Column(Boolean, default=False, nullable=False)

    participants = relationship("ConversationParticipant", back_populates="conversation")
    messages = relationship("Message", back_populates="conversation")


class ConversationParticipant(BaseModel):
    __tablename__ = "conversation_participants"

    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)

    conversation = relationship("Conversation", back_populates="participants")


class Message(BaseModel):
    __tablename__ = "messages"

    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=False)
    sender_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    body = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)

    conversation = relationship("Conversation", back_populates="messages")


class Notification(BaseModel):
    __tablename__ = "notifications"

    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=True)
    is_read = Column(Boolean, default=False, nullable=False)
    link = Column(String(300), nullable=True)


class Announcement(BaseModel):
    __tablename__ = "announcements"

    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    target_role = Column(String(50), nullable=True)   # null = everyone; else a role name


class Meeting(BaseModel):
    """Parent-teacher meeting requests."""

    __tablename__ = "meetings"

    requested_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    teacher_id = Column(String(36), ForeignKey("teacher_profiles.id"), nullable=True)
    student_id = Column(String(36), ForeignKey("student_profiles.id"), nullable=True)
    reason = Column(Text, nullable=True)
    requested_time = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), default="pending", nullable=False)   # pending, confirmed, completed, cancelled


class PTAMeeting(BaseModel):
    __tablename__ = "pta_meetings"

    title = Column(String(255), nullable=False)
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    minutes = Column(Text, nullable=True)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)
