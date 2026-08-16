"""
Authentication state management.

Auth state lives in st.session_state, which is per-browser-session and safe
for this purpose, but the *authoritative* facts (who the user is, what
roles/permissions they hold, whether the account is active) are re-read
from the database on every login and on every permission check that
matters -- session_state alone is never treated as proof of authorization.
"""

from datetime import datetime, timedelta, timezone

import streamlit as st
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from config.settings import settings
from database.connection import get_session
from models.user import User, Role


SESSION_USER_ID = "auth_user_id"
SESSION_LOGIN_AT = "auth_login_at"


def _now():
    return datetime.now(timezone.utc)


def login(user: User) -> None:
    st.session_state[SESSION_USER_ID] = user.id
    st.session_state[SESSION_LOGIN_AT] = _now().isoformat()


def logout() -> None:
    for key in (SESSION_USER_ID, SESSION_LOGIN_AT):
        st.session_state.pop(key, None)


def _session_expired() -> bool:
    login_at_raw = st.session_state.get(SESSION_LOGIN_AT)
    if not login_at_raw:
        return True
    login_at = datetime.fromisoformat(login_at_raw)
    return _now() - login_at > timedelta(minutes=settings.session_timeout_minutes)


def get_current_user() -> User | None:
    """
    Re-fetches the user from the database on every call so a change in role,
    status, or permissions takes effect immediately -- never trusts a cached
    copy of the user object across reruns.
    """
    user_id = st.session_state.get(SESSION_USER_ID)
    if not user_id:
        return None
    if _session_expired():
        logout()
        return None

    db = get_session()
    try:
        stmt = (
            select(User)
            .options(joinedload(User.roles).joinedload(Role.permissions))
            .where(User.id == user_id)
        )
        user = db.execute(stmt).unique().scalar_one_or_none()
        if user is None or user.status != "active":
            logout()
            return None
        db.expunge_all()  # detach cleanly; roles/permissions already loaded above
        return user
    finally:
        db.close()


def is_authenticated() -> bool:
    return get_current_user() is not None


def require_login():
    """Call at the top of any protected page. Stops rendering if not authenticated."""
    user = get_current_user()
    if user is None:
        st.warning("Please log in to continue.")
        st.stop()
    return user
