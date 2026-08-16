"""Shared declarative base and mixins used by every model."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Boolean, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


def new_uuid() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    """Adds created/updated metadata to every table that uses it."""

    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class SoftDeleteMixin:
    """Adds soft-deletion support so records are deactivated, not destroyed."""

    is_active = Column(Boolean, default=True, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)


class BaseModel(Base, TimestampMixin, SoftDeleteMixin):
    __abstract__ = True

    id = Column(String(36), primary_key=True, default=new_uuid)
