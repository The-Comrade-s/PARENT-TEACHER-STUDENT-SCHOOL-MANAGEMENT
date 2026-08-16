"""
Role-based access control.

Rule: the interface may hide a button, but every sensitive operation must
also check the authenticated user's role/permissions here before acting.
Never trust a role value coming from a widget or URL parameter.
"""

import streamlit as st

from auth.session import get_current_user
from models.user import User

# Canonical system roles. Additional roles can be added later via the Role table
# without changing this constant -- these five are simply the ones every
# permission check in this phase understands by name.
ROLE_SUPER_ADMIN = "super_admin"
ROLE_SCHOOL_ADMIN = "school_admin"
ROLE_TEACHER = "teacher"
ROLE_PARENT = "parent"
ROLE_STUDENT = "student"

ALL_ROLES = [ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN, ROLE_TEACHER, ROLE_PARENT, ROLE_STUDENT]

ROLE_DISPLAY_NAMES = {
    ROLE_SUPER_ADMIN: "Super Administrator",
    ROLE_SCHOOL_ADMIN: "School Administrator",
    ROLE_TEACHER: "Teacher",
    ROLE_PARENT: "Parent",
    ROLE_STUDENT: "Student",
}


def user_has_role(user: User | None, *role_names: str) -> bool:
    if user is None:
        return False
    return any(user.has_role(r) for r in role_names)


def user_has_permission(user: User | None, permission_code: str) -> bool:
    if user is None:
        return False
    if user_has_role(user, ROLE_SUPER_ADMIN):
        return True  # super admin implicitly holds every permission
    return user.has_permission(permission_code)


def require_role(*role_names: str) -> User:
    """
    Call at the top of a page/action. Stops execution with an error if the
    authenticated user does not hold one of the given roles.
    """
    user = get_current_user()
    if user is None:
        st.warning("Please log in to continue.")
        st.stop()
    if not user_has_role(user, *role_names):
        st.error("You do not have permission to access this page.")
        st.stop()
    return user


def require_permission(permission_code: str) -> User:
    user = get_current_user()
    if user is None:
        st.warning("Please log in to continue.")
        st.stop()
    if not user_has_permission(user, permission_code):
        st.error("You do not have permission to perform this action.")
        st.stop()
    return user
