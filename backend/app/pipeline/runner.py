"""Run orchestration: fetch sources in parallel, then ingest results one source at a time."""

from __future__ import annotations

import sqlite3
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from typing import Any

from ..config import AppConfig
from ..core.errors import ConflictError
from ..db import open_db
from ..db.repositories import health_state, run_lock, runs
from ..llm import LlmError, create_client, load_llm_settings
from ..sources import FetchContext, fetch_source, resolve_enabled_sources
from .ingest import SeenIndex, process_batch
from .llm_pass import run_llm_pass
from .progress import RunProgress

MAX_PARALLEL_FETCHES = 6


def _now() -> str:
    return datetime.now(UTC).isoformat()


def select_sources(config: AppConfig, only: list[str] | None) -> list[dict[str, Any]]:
    sources = resolve_enabled_sources(config)
    if only:
        wanted = set(only)
        sources = [source for source in sources if source["id"] in wanted]
    return sources


def begin_run(conn: sqlite3.Connection, trigger: str, force: bool = False) -> tuple[int, str]:
    """Take the single-flight lock and open a run record. Raises ConflictError if one is active."""
    acquired, message = run_lock.acquire(conn, force)
    if not acquired:
        raise ConflictError(message or "another run is active")
    try:
        return runs.create(conn, trigger)
    except Exception:
        run_lock.release(conn)
        raise


def _llm_stage(conn: sqlite3.Connection, profile: dict[str, Any]) -> dict[str, Any] | None:
    """The optional AI pass. A failure here is reported, never raised: the fetch already succeeded."""
    settings = load_llm_settings()
    if not settings.enabled:
        return None
    try:
        return run_llm_pass(conn, create_client(settings), profile)
    except LlmError as exc:
        return {"assessed": 0, "failed": 0, "message": str(exc)}


def execute_run(
    conn: sqlite3.Connection,
    config: AppConfig,
    run_id: int,
    started: str,
    sources: list[dict[str, Any]],
    dry_run: bool,
    progress: RunProgress | None = None,
) -> dict[str, Any]:
    """Fetch in parallel, store sequentially. The caller holds the run lock; it is always released here."""
    per_source: dict[str, dict[str, Any]] = {}
    try:
        profile = {**config.profile, "blockedCompanies": config.companies.get("blocked", [])}
        ctx = FetchContext.from_config(config)
        index = SeenIndex.from_db(conn)

        with ThreadPoolExecutor(max_workers=MAX_PARALLEL_FETCHES) as pool:
            futures = {pool.submit(fetch_source, source, ctx): source for source in sources}
            for future in as_completed(futures):
                source, result = futures[future], future.result()
                run_lock.touch(conn)
                stats: dict[str, Any] = {
                    "fetched": 0, "new": 0, "known": 0, "skipped": 0,
                    "error": result.error, "duration_ms": result.duration_ms,
                }
                if not result.error:
                    try:
                        stats.update(process_batch(conn, result.records, source, profile, index, _now(), dry_run))
                    except Exception as exc:  # a bad record must not abort the other sources
                        stats["error"] = f"{type(exc).__name__}: {exc}"

                per_source[source["id"]] = stats
                now = _now()
                health_state.record_companies(conn, result.companies, now)
                health_state.record_source(conn, source["id"], stats["error"], now)
                if progress:
                    progress.update_source(source["id"], state="error" if stats["error"] else "ok", **stats)

        llm_stats = None
        if not dry_run:
            if progress:
                progress.set_stage("ai")
            llm_stats = _llm_stage(conn, profile)

        finished = runs.finish(conn, run_id, {"sources": per_source, "llm": llm_stats})
        runs.record_sources(conn, run_id, per_source)
        if progress:
            progress.finish(llm=llm_stats)
        return {
            "status": "ok",
            "run_id": run_id,
            "started_at": started,
            "finished_at": finished,
            "dry_run": dry_run,
            "per_source": per_source,
            "llm": llm_stats,
        }
    except Exception as exc:
        message = f"{type(exc).__name__}: {exc}"
        runs.finish(conn, run_id, {"error": message, "sources": per_source})
        if progress:
            progress.finish(error=message)
        raise
    finally:
        run_lock.release(conn)


def run_fetch(
    config: AppConfig,
    only: list[str] | None = None,
    dry_run: bool = False,
    force: bool = False,
    trigger: str = "cli",
) -> dict[str, Any]:
    """Run a full fetch synchronously (the CLI path). Returns a summary."""
    conn = open_db()
    try:
        try:
            run_id, started = begin_run(conn, trigger, force)
        except ConflictError as exc:
            return {"status": "blocked", "message": str(exc)}
        return execute_run(conn, config, run_id, started, select_sources(config, only), dry_run)
    finally:
        conn.close()
