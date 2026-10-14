"""Per-source and per-company health recorded by runs and board checks."""

from __future__ import annotations

import sqlite3
from typing import Any


def record_source(conn: sqlite3.Connection, source_id: str, error: str | None, now: str) -> None:
    if error is None:
        conn.execute(
            """INSERT INTO source_state (source_id, last_run_at, last_status, last_error, last_success_at)
               VALUES (?, ?, 'ok', NULL, ?)
               ON CONFLICT(source_id) DO UPDATE SET
                 last_run_at = excluded.last_run_at,
                 last_status = 'ok',
                 last_error = NULL,
                 last_success_at = excluded.last_success_at""",
            (source_id, now, now),
        )
    else:
        conn.execute(
            """INSERT INTO source_state (source_id, last_run_at, last_status, last_error)
               VALUES (?, ?, 'error', ?)
               ON CONFLICT(source_id) DO UPDATE SET
                 last_run_at = excluded.last_run_at,
                 last_status = 'error',
                 last_error = excluded.last_error""",
            (source_id, now, error),
        )
    conn.commit()


def source_states(conn: sqlite3.Connection) -> dict[str, sqlite3.Row]:
    return {row["source_id"]: row for row in conn.execute("SELECT * FROM source_state")}


def record_companies(conn: sqlite3.Connection, companies: list[dict[str, Any]], now: str) -> None:
    for company in companies:
        conn.execute(
            """INSERT INTO company_state (company_key, last_checked_at, last_error, open_roles)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(company_key) DO UPDATE SET
                 last_checked_at = excluded.last_checked_at,
                 last_error = excluded.last_error,
                 open_roles = CASE WHEN excluded.last_error IS NULL THEN excluded.open_roles ELSE open_roles END""",
            (company["key"], now, company["error"], company["open_roles"]),
        )
    conn.commit()


def company_states(conn: sqlite3.Connection) -> dict[str, sqlite3.Row]:
    return {row["company_key"]: row for row in conn.execute("SELECT * FROM company_state")}
