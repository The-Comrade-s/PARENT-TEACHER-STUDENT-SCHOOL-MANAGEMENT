"""Notifications and announcements, persisted so they survive page refresh."""

from sqlalchemy import select

from database.connection import get_session
from models.communication import Notification, Announcement
from models.user import User, Role, user_roles


def create_notification(user_id: str, title: str, body: str = "", link: str = "") -> None:
    db = get_session()
    try:
        db.add(Notification(user_id=user_id, title=title, body=body, link=link or None))
        db.commit()
    finally:
        db.close()


def list_notifications(user_id: str, unread_only: bool = False) -> list[Notification]:
    db = get_session()
    try:
        stmt = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            stmt = stmt.where(Notification.is_read == False)  # noqa: E712
        stmt = stmt.order_by(Notification.created_at.desc())
        return list(db.execute(stmt).scalars().all())
    finally:
        db.close()


def mark_notification_read(notification_id: str) -> None:
    db = get_session()
    try:
        n = db.get(Notification, notification_id)
        if n is not None:
            n.is_read = True
            db.commit()
    finally:
        db.close()


def mark_all_read(user_id: str) -> None:
    db = get_session()
    try:
        db.execute(
            Notification.__table__.update().where(Notification.user_id == user_id).values(is_read=True)
        )
        db.commit()
    finally:
        db.close()


def create_announcement(created_by: str, title: str, body: str, target_role: str | None = None) -> tuple[bool, str]:
    if not title.strip() or not body.strip():
        return False, "Title and body are required."
    db = get_session()
    try:
        announcement = Announcement(created_by=created_by, title=title.strip(), body=body.strip(), target_role=target_role)
        db.add(announcement)
        db.flush()

        # Fan out a notification to every targeted user.
        stmt = select(User)
        if target_role:
            stmt = (
                stmt.join(user_roles, User.id == user_roles.c.user_id)
                .join(Role, Role.id == user_roles.c.role_id)
                .where(Role.name == target_role)
            )
        users = db.execute(stmt).unique().scalars().all()
        for u in users:
            db.add(Notification(user_id=u.id, title=f"Announcement: {title.strip()}", body=body.strip()))

        db.commit()
        return True, "Announcement published."
    finally:
        db.close()


def list_announcements() -> list[Announcement]:
    db = get_session()
    try:
        return list(db.execute(select(Announcement).order_by(Announcement.created_at.desc())).scalars().all())
    finally:
        db.close()
