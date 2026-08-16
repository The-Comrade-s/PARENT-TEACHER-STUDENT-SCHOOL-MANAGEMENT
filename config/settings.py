"""
Central configuration.

Values are resolved in this order:
1. Streamlit secrets (st.secrets) - used in deployed environments
2. Environment variables (.env via python-dotenv) - used for local dev
3. Safe local defaults (SQLite) - so the app runs out of the box

Never hardcode real secrets here. This module only defines how to find them.
"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _get(key: str, default: str = "") -> str:
    """Resolve a config value from Streamlit secrets first, then env vars."""
    try:
        import streamlit as st

        if key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return os.getenv(key, default)


@dataclass(frozen=True)
class Settings:
    app_name: str = "Parent-Teacher Communication and Student Monitoring System"
    app_short_name: str = "PTMS"

    database_url: str = _get("DATABASE_URL", "sqlite:///./ptms_local.db")

    secret_key: str = _get("SECRET_KEY", "dev-only-change-me-in-production")

    session_timeout_minutes: int = int(_get("SESSION_TIMEOUT_MINUTES", "60"))
    max_failed_login_attempts: int = int(_get("MAX_FAILED_LOGIN_ATTEMPTS", "5"))
    account_lock_minutes: int = int(_get("ACCOUNT_LOCK_MINUTES", "15"))

    min_password_length: int = int(_get("MIN_PASSWORD_LENGTH", "8"))

    default_admin_email: str = _get("DEFAULT_ADMIN_EMAIL", "admin@ptms.local")
    default_admin_password: str = _get("DEFAULT_ADMIN_PASSWORD", "ChangeMe123!")

    # Branding
    color_primary: str = "#0B3D91"      # deep blue
    color_primary_light: str = "#1F5FBF"
    color_background: str = "#F7F7F2"   # off-white
    color_surface: str = "#FFFFFF"
    color_text: str = "#111111"         # near black
    color_neutral: str = "#6B7280"

    environment: str = _get("ENVIRONMENT", "development")


settings = Settings()
