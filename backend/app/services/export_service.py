"""Export jobs as a downloadable file."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

from ..core.errors import InvalidInputError
from ..db.repositories import jobs as repo
from ..domain.export import jobs_to_csv, jobs_to_markdown

FORMATS = {
    "csv": ("text/csv; charset=utf-8", "csv", jobs_to_csv),
    "markdown": ("text/markdown; charset=utf-8", "md", jobs_to_markdown),
}


def export_jobs(conn: sqlite3.Connection, fmt: str, statuses: tuple[str, ...]) -> tuple[str, str, str]:
    """Returns (body, media type, suggested filename)."""
    if fmt not in FORMATS:
        raise InvalidInputError(f"Unknown format '{fmt}'. Use csv or markdown.")
    unknown = [status for status in statuses if status not in repo.STATUSES]
    if unknown:
        raise InvalidInputError(f"Unknown status: {', '.join(unknown)}")

    media_type, extension, render = FORMATS[fmt]
    body = render(repo.export_rows(conn, statuses))
    return body, media_type, f"jobradar-{datetime.now(UTC):%Y-%m-%d}.{extension}"
