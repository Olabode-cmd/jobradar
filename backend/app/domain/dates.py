"""Date parsing shared by normalization, rules and scoring."""

from __future__ import annotations

from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Any


def parse_datetime(value: str) -> datetime | None:
    """Parse ISO-8601 or RFC 2822 dates; naive dates become UTC-aware."""
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        try:
            dt = parsedate_to_datetime(str(value))
        except (TypeError, ValueError):
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt


def to_iso(value: Any) -> str | None:
    """ISO-8601 UTC string from ISO/RFC 2822 text or an epoch (seconds or milliseconds)."""
    if value is None or value == "" or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        seconds = value / 1000 if value > 1e11 else value
        try:
            return datetime.fromtimestamp(seconds, UTC).isoformat()
        except (OverflowError, OSError, ValueError):
            return None
    parsed = parse_datetime(str(value))
    return parsed.astimezone(UTC).isoformat() if parsed else None
