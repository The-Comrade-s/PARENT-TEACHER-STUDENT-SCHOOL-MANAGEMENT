"""Audit log search and filtering. Writing happens via services.auth_service.log_action."""

from datetime import datetime

from sqlalchemy import select

from database.connection import get_session
from models.user import AuditLog


def search_audit_log(user_email: str = "", module: str = "", action: str = "",
                      start_date: datetime | None = None, end_date: datetime | None = None,
                      limit: int = 200) -> list[AuditLog]:
    db = get_session()
    try:
        stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
        if user_email:
            stmt = stmt.where(AuditLog.user_email.ilike(f"%{user_email}%"))
        if module:
            stmt = stmt.where(AuditLog.module == module)
        if action:
            stmt = stmt.where(AuditLog.action.ilike(f"%{action}%"))
        if start_date:
            stmt = stmt.where(AuditLog.created_at >= start_date)
        if end_date:
            stmt = stmt.where(AuditLog.created_at <= end_date)
        return list(db.execute(stmt).scalars().all())
    finally:
        db.close()


def list_distinct_modules() -> list[str]:
    db = get_session()
    try:
        rows = db.execute(select(AuditLog.module).distinct()).all()
        return sorted({r[0] for r in rows if r[0]})
    finally:
        db.close()
