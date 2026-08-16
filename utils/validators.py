"""
Shared validation helpers.

Every form in this application validates on the server side using these
functions (or equivalent checks in the owning service) -- Streamlit widget
constraints (min_value, required, etc.) are a UX convenience, never the
only line of defense.
"""

import re

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email(email: str) -> bool:
    return bool(EMAIL_PATTERN.match(email.strip())) if email else False


def is_non_empty(value: str) -> bool:
    return bool(value and value.strip())


def is_valid_score(score: float, minimum: float = 0, maximum: float = 100) -> bool:
    try:
        return minimum <= float(score) <= maximum
    except (TypeError, ValueError):
        return False


def is_future_or_today(target_date, today) -> bool:
    return target_date >= today


def is_positive_integer(value) -> bool:
    try:
        return int(value) > 0
    except (TypeError, ValueError):
        return False


def sanitize_text(value: str, max_length: int = 2000) -> str:
    """Strips and truncates free-text input to a safe length before storage."""
    if not value:
        return ""
    return value.strip()[:max_length]
