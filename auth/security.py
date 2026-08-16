"""Password hashing and verification. Passwords are never stored in plain text."""

import bcrypt


def hash_password(plain_password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def password_meets_policy(password: str, min_length: int = 8) -> tuple[bool, str]:
    """Returns (is_valid, message). Checked server-side, never trusting the widget alone."""
    if len(password) < min_length:
        return False, f"Password must be at least {min_length} characters long."
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter."
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter."
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number."
    return True, ""
