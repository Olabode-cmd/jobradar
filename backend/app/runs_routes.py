"""Run-now and run history endpoints. A run executes in a background thread."""

from __future__ import annotations

import json
import logging
import threading
from typing import Any

from fastapi import APIRouter, HTTPException

from .config import AppConfig, load_config
from .db import open_db
from .pipeline import acquire_run_lock, create_run, execute_run, release_run_lock, select_sources
from .run_progress import PROGRESS
from .schemas import RunStartIn

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/runs", tags=["runs"])

HISTORY_LIMIT = 30


def _run_in_background(
    config: AppConfig, run_id: int, started: str, sources: list[dict[str, Any]], dry_run: bool
) -> None:
    conn = open_db()
    try:
        execute_run(conn, config, run_id, started, sources, dry_run, update_progress=True)
    except Exception:
        logger.exception("run %s failed", run_id)
    finally:
        conn.close()


@router.post("", status_code=202)
def start_run(body: RunStartIn) -> dict[str, Any]:
    config = load_config()
    sources = select_sources(config, body.sources)
    if body.sources:
        unknown = set(body.sources) - {source["id"] for source in sources}
        if unknown:
            raise HTTPException(status_code=422, detail=f"Unknown or disabled sources: {', '.join(sorted(unknown))}")
    if not sources:
        raise HTTPException(status_code=422, detail="No sources are enabled. Enable one on the Sources page.")

    conn = open_db()
    try:
        acquired, message = acquire_run_lock(conn, force=False)
        if not acquired:
            raise HTTPException(status_code=409, detail=message)
        try:
            run_id, started = create_run(conn, "dashboard")
        except Exception:
            release_run_lock(conn)
            raise
    finally:
        conn.close()

    PROGRESS.start(run_id, started, [source["id"] for source in sources], body.dry_run)
    threading.Thread(
        target=_run_in_background,
        args=(config, run_id, started, sources, body.dry_run),
        name=f"run-{run_id}",
        daemon=True,
    ).start()
    return {"run_id": run_id}


@router.get("/current")
def current_run() -> dict[str, Any]:
    return PROGRESS.snapshot() or {"state": "idle"}


@router.get("")
def run_history() -> dict[str, Any]:
    conn = open_db()
    try:
        rows = conn.execute("SELECT * FROM runs ORDER BY id DESC LIMIT ?", (HISTORY_LIMIT,)).fetchall()
        items = []
        for row in rows:
            try:
                summary = json.loads(row["summary"] or "{}")
            except json.JSONDecodeError:
                summary = {}
            per_source = summary if isinstance(summary, dict) and "error" not in summary else summary.get("sources", {})
            sources = [
                {"id": source_id, **stats}
                for source_id, stats in per_source.items()
                if isinstance(stats, dict)
            ]
            items.append(
                {
                    "id": row["id"],
                    "started_at": row["started_at"],
                    "finished_at": row["finished_at"],
                    "trigger": row["trigger"],
                    "error": summary.get("error") if isinstance(summary, dict) and isinstance(summary.get("error"), str) else None,
                    "sources": sources,
                    "new": sum(int(source.get("new") or 0) for source in sources),
                }
            )
        return {"items": items}
    finally:
        conn.close()
