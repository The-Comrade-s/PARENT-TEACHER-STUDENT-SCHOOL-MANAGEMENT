"""
Shared pytest fixtures.

Tests run against an isolated in-memory SQLite database so they never
touch a real deployment's data, and each test gets a clean schema.
"""

import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import pytest


@pytest.fixture(autouse=True)
def _fresh_database(monkeypatch):
    """Creates a fresh in-memory database engine/session factory for every test."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    import database.connection as connection

    test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    test_session_local = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)

    monkeypatch.setattr(connection, "engine", test_engine)
    monkeypatch.setattr(connection, "SessionLocal", test_session_local)

    from models.base import Base
    import models.user  # noqa: F401
    import models.school  # noqa: F401
    import models.people  # noqa: F401
    import models.academic  # noqa: F401
    import models.communication  # noqa: F401
    import models.security  # noqa: F401
    import models.settings  # noqa: F401

    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
