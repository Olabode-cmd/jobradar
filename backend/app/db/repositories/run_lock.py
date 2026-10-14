"""Single-flight run lock stored in the meta table, with a heartbeat so a crash can't wedge it."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime, timedelta

from ...domain.dates import parse_datetime

LOCK_KEY = "active_run"
STALE_AFTER_S = 600


def _now() -> str:
    return datetime.now(UTC).isoformat()


def acquire(conn: sqlite3.Connection, force: bool) -> tuple[bool, str | None]:
    row = conn.execute("SELECT value FROM meta WHERE key = ?", (LOCK_KEY,)).fetchone()
    if row is not None:
        payload = json.loads(row["value"])
        heartbeat = parse_datetime(payload["heartbeat"])
        fresh = heartbeat is not None and datetime.now(UTC) - heartbeat < timedelta(seconds=STALE_AFTER_S)
        if fresh and not force:
            return False, (
                f"another run is active (started {payload['started_at']}); "
                "wait for it to finish or use --force"
            )
    payload = {"started_at": _now(), "heartbeat": _now()}
    conn.execute(
        "INSERT INTO meta (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (LOCK_KEY, json.dumps(payload)),
    )
    conn.commit()
    return True, None


def touch(conn: sqlite3.Connection) -> None:
    row = conn.execute("SELECT value FROM meta WHERE key = ?", (LOCK_KEY,)).fetchone()
    if row is None:
        return
    payload = json.loads(row["value"])
    payload["heartbeat"] = _now()
    conn.execute("UPDATE meta SET value = ? WHERE key = ?", (json.dumps(payload), LOCK_KEY))
    conn.commit()


def release(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM meta WHERE key = ?", (LOCK_KEY,))
    conn.commit()
