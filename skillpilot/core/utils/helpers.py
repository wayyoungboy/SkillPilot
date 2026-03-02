"""Helper utilities"""

from datetime import UTC, datetime
from uuid import uuid4


def generate_id(prefix: str = "") -> str:
    """
    Generate a unique ID with optional prefix.

    Args:
        prefix: Optional prefix for the ID (e.g., "sk_", "usr_")

    Returns:
        Generated ID string
    """
    unique_part = uuid4().hex[:12]
    return f"{prefix}{unique_part}" if prefix else unique_part


def utc_now() -> datetime:
    """
    Get current UTC time as timezone-aware datetime.

    Returns:
        Current UTC datetime
    """
    return datetime.now(UTC)


def sanitize_string(value: str | None, max_length: int = 1000) -> str | None:
    """
    Sanitize a string value.

    Args:
        value: String to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized string or None
    """
    if value is None:
        return None

    # Strip whitespace
    value = value.strip()

    # Truncate if too long
    if len(value) > max_length:
        value = value[:max_length]

    return value
