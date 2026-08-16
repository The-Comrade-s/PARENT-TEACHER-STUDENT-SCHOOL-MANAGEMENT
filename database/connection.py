"""
Database engine and session management.

The database is the single source of truth for all permanent data.
Streamlit session_state is only ever used for transient UI/auth state,
never as a substitute for persisted records.
"""

import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from config.settings import settings

_connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(
    settings.database_url,
    connect_args=_connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_session() -> Session:
    """Return a new SQLAlchemy session. Caller is responsible for closing it."""
    return SessionLocal()


@st.cache_resource
def init_database():
    """
    Create all tables if they do not exist yet.
    Cached so it only runs once per app process — never drops or recreates
    existing tables, so normal app startup never destroys data.
    """
    from models.base import Base
    import models.user  # noqa: F401
    import models.school  # noqa: F401
    import models.people  # noqa: F401
    import models.academic  # noqa: F401
    import models.communication  # noqa: F401
    import models.security  # noqa: F401
    import models.settings  # noqa: F401

    Base.metadata.create_all(bind=engine)
    return True
