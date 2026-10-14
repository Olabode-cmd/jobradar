"""Starting runs from the dashboard (in a background thread) and reading their progress."""

from __future__ import annotations

import logging
import sqlite3
import threading
from typing import Any

from ..config import AppConfig, load_config
from ..core.errors import InvalidInputError
from ..db import open_db
from ..db.repositories import runs
from ..pipeline import PROGRESS, begin_run, execute_run, select_sources

logger = logging.getLogger(__name__)


def _run_in_background(
    config: AppConfig, run_id: int, started: str, sources: list[dict[str, Any]], dry_run: bool
) -> None:
    conn = open_db()
    try:
        execute_run(conn, config, run_id, started, sources, dry_run, progress=PROGRESS)
    except Exception:
        logger.exception("run %s failed", run_id)
    finally:
        conn.close()


def start_run(source_ids: list[str] | None, dry_run: bool) -> dict[str, int]:
    config = load_config()
    sources = select_sources(config, source_ids)
    if source_ids:
        unknown = set(source_ids) - {source["id"] for source in sources}
        if unknown:
            raise InvalidInputError(f"Unknown or disabled sources: {', '.join(sorted(unknown))}")
    if not sources:
        raise InvalidInputError("No sources are enabled. Enable one on the Sources page.")

    conn = open_db()
    try:
        run_id, started = begin_run(conn, "dashboard")
    finally:
        conn.close()

    PROGRESS.start(run_id, started, [source["id"] for source in sources], dry_run)
    threading.Thread(
        target=_run_in_background,
        args=(config, run_id, started, sources, dry_run),
        name=f"run-{run_id}",
        daemon=True,
    ).start()
    return {"run_id": run_id}


def current_run() -> dict[str, Any]:
    return PROGRESS.snapshot() or {"state": "idle"}


def run_history(conn: sqlite3.Connection) -> dict[str, Any]:
    return {"items": runs.history(conn)}
