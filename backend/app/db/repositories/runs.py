"""Run history."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from typing import Any

HISTORY_LIMIT = 30


def _now() -> str:
    return datetime.now(UTC).isoformat()


def create(conn: sqlite3.Connection, trigger: str) -> tuple[int, str]:
    started = _now()
    cur = conn.execute("INSERT INTO runs (started_at, trigger, summary) VALUES (?, ?, '{}')", (started, trigger))
    conn.commit()
    return cur.lastrowid, started


def finish(conn: sqlite3.Connection, run_id: int, summary: dict[str, Any]) -> str:
    finished = _now()
    conn.execute("UPDATE runs SET finished_at = ?, summary = ? WHERE id = ?", (finished, json.dumps(summary), run_id))
    conn.commit()
    return finished


def record_sources(conn: sqlite3.Connection, run_id: int, per_source: dict[str, dict[str, Any]]) -> None:
    for source_id, stats in per_source.items():
        conn.execute(
            "INSERT INTO run_sources (run_id, source_id, fetched, new, errors, duration_ms) VALUES (?, ?, ?, ?, ?, ?)",
            (run_id, source_id, stats["fetched"], stats["new"], 1 if stats.get("error") else 0, stats["duration_ms"]),
        )
    conn.commit()


def history(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    items = []
    for row in conn.execute("SELECT * FROM runs ORDER BY id DESC LIMIT ?", (HISTORY_LIMIT,)):
        try:
            summary = json.loads(row["summary"] or "{}")
        except json.JSONDecodeError:
            summary = {}
        failed = isinstance(summary, dict) and isinstance(summary.get("error"), str)
        per_source = summary.get("sources", {}) if failed else summary
        sources = [{"id": sid, **stats} for sid, stats in per_source.items() if isinstance(stats, dict)]
        items.append(
            {
                "id": row["id"],
                "started_at": row["started_at"],
                "finished_at": row["finished_at"],
                "trigger": row["trigger"],
                "error": summary["error"] if failed else None,
                "sources": sources,
                "new": sum(int(source.get("new") or 0) for source in sources),
            }
        )
    return items
