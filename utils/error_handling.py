"""
Error handling.

Streamlit pages should never surface a raw exception, SQL error, stack
trace, or file path to an ordinary user. Use safe_call to wrap risky
operations: the real exception is logged for developers, and the user
sees a plain, non-technical message instead.
"""

import logging
import traceback

logger = logging.getLogger("ptms")
logging.basicConfig(level=logging.WARNING)


def log_technical_error(context: str, exc: Exception) -> None:
    """Logs full technical detail server-side only; never shown to the end user."""
    logger.error("[%s] %s\n%s", context, exc, traceback.format_exc())


def safe_call(func, *args, context: str = "operation", user_message: str = "", **kwargs):
    """
    Runs func(*args, **kwargs). On success returns (True, result).
    On failure, logs the real exception and returns (False, safe_message)
    where safe_message never contains internal details.
    """
    try:
        return True, func(*args, **kwargs)
    except Exception as exc:  # noqa: BLE001 - intentional: this is the top-level safety net
        log_technical_error(context, exc)
        message = user_message or "Something went wrong while processing your request. Please try again."
        return False, message
