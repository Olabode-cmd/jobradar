"""Pipeline: fetch → normalize → dedupe → rules → store, with a single-flight run lock.

Store-then-filter: every fetched job is stored with its eligibility computed at
insert time; the dashboard filters at query time. This makes profile tuning and
audit ("what did RemoteOK drop today?") possible.
"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime, timedelta
from typing import Any

from .config import AppConfig
from .db import open_db
from .normalize import is_usable, normalize_job
from .rules import apply_rules, parse_datetime, score_job
from .run_progress import PROGRESS
from .sources.drivers import fetch_source, resolve_enabled_sources

LOCK_KEY = "active_run"
STALE_AFTER_S = 600  # a crashed run releases itself after 10 minutes
REPOST_DAYS = 30
MAX_PARALLEL_FETCHES = 6


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _parse_dt(value: str) -> datetime:
    dt = parse_datetime(value)
    if dt is None:
        raise ValueError(f"unparseable date: {value}")
    return dt


def acquire_run_lock(conn: Any, force: bool) -> tuple[bool, str | None]:
    row = conn.execute("SELECT value FROM meta WHERE key = ?", (LOCK_KEY,)).fetchone()
    if row is not None:
        payload = json.loads(row["value"])
        heartbeat = _parse_dt(payload["heartbeat"])
        fresh = datetime.now(UTC) - heartbeat < timedelta(seconds=STALE_AFTER_S)
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


def touch_run_lock(conn: Any) -> None:
    row = conn.execute("SELECT value FROM meta WHERE key = ?", (LOCK_KEY,)).fetchone()
    if row is None:
        return
    payload = json.loads(row["value"])
    payload["heartbeat"] = _now()
    conn.execute("UPDATE meta SET value = ? WHERE key = ?", (json.dumps(payload), LOCK_KEY))
    conn.commit()


def release_run_lock(conn: Any) -> None:
    conn.execute("DELETE FROM meta WHERE key = ?", (LOCK_KEY,))
    conn.commit()


def _attach_source(conn: Any, job_id: int, source_id: str, url: str, now: str) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO job_sources (job_id, source_id, url, seen_at) VALUES (?, ?, ?, ?)",
        (job_id, source_id, url, now),
    )


def _maybe_repost(conn: Any, job_id: int, posted_at: str | None, now: str) -> None:
    """A duplicate arriving with a much newer posted date re-opens as New."""
    if not posted_at:
        return
    row = conn.execute("SELECT status, status_changed_at, first_seen_at FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if row is None or row["status"] == "new":
        return
    try:
        posted = _parse_dt(posted_at)
        changed = _parse_dt(row["status_changed_at"] or row["first_seen_at"] or now)
        if posted > changed + timedelta(days=REPOST_DAYS):
            conn.execute(
                "UPDATE jobs SET status = 'new', reposted = 1, status_changed_at = ? WHERE id = ?",
                (now, job_id),
            )
    except ValueError:
        pass


def _insert_job(conn: Any, job: dict[str, Any], now: str) -> int:
    cur = conn.execute(
        """
        INSERT INTO jobs (
            canonical_url, dedupe_hash, company_key, company_id, company, title,
            location_text, remote_status, region_restrictions, posted_at, first_seen_at,
            apply_url, apply_method, emails, salary_text, description, score, score_reasons,
            llm_result, eligibility, status, status_changed_at, low_confidence
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'new', ?, ?)
        """,
        (
            job["canonical_url"], job["dedupe_hash"], job["company_key"], job.get("company_id"),
            job["company"], job["title"], job["location_text"], job["remote_status"],
            json.dumps(job["region_restrictions"]) if job.get("region_restrictions") else None,
            job["posted_at"], job["first_seen_at"], job["apply_url"], job["apply_method"],
            job["emails"], job["salary_text"], job["description"], job["score"],
            json.dumps(job["score_reasons"]) if job.get("score_reasons") else None,
            json.dumps(job["llm_result"]) if job.get("llm_result") else None,
            job["eligibility"], now, 1 if job.get("low_confidence") else 0,
        ),
    )
    conn.commit()
    return cur.lastrowid


def _record_source_state(conn: Any, source_id: str, status: str, error: str | None, now: str) -> None:
    if status == "ok":
        conn.execute(
            """INSERT INTO source_state (source_id, last_run_at, last_status, last_error, last_success_at)
               VALUES (?, ?, ?, NULL, ?)
               ON CONFLICT(source_id) DO UPDATE SET
                 last_run_at = excluded.last_run_at,
                 last_status = 'ok',
                 last_error = NULL,
                 last_success_at = excluded.last_success_at""",
            (source_id, now, "ok", now),
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


def process_batch(
    conn: Any,
    records: list[dict[str, Any]],
    source: dict[str, Any],
    profile: dict[str, Any],
    seen_urls: set[str],
    seen_hashes: set[str],
    url_to_id: dict[str, int],
    hash_to_id: dict[str, int],
    now: str,
    dry_run: bool,
) -> dict[str, int]:
    """Normalize, dedupe and store one source's records. Returns fetched/new counts."""
    stats = {"fetched": len(records), "new": 0, "known": 0, "skipped": 0}

    for raw in records:
        if not is_usable(raw):
            stats["skipped"] += 1
            continue
        job = normalize_job(raw, source, now)
        url = job["canonical_url"]
        h = job["dedupe_hash"]

        if url in seen_urls or url in url_to_id:
            existing = url_to_id.get(url)
            if existing:
                _maybe_repost(conn, existing, job["posted_at"], now)
                _attach_source(conn, existing, source["id"], url, now)
            stats["known"] += 1
            continue

        if h and (h in seen_hashes or h in hash_to_id):
            existing = hash_to_id.get(h)
            if existing:
                _maybe_repost(conn, existing, job["posted_at"], now)
                _attach_source(conn, existing, source["id"], url, now)
            stats["known"] += 1
            continue

        job["eligibility"] = apply_rules(job, profile)
        job["score"], job["score_reasons"] = score_job(job, profile)

        if dry_run:
            seen_urls.add(url)
            if h:
                seen_hashes.add(h)
            stats["new"] += 1
            continue

        job_id = _insert_job(conn, job, now)
        seen_urls.add(url)
        if h:
            seen_hashes.add(h)
        url_to_id[url] = job_id
        if h:
            hash_to_id[h] = job_id
        _attach_source(conn, job_id, source["id"], url, now)
        stats["new"] += 1

    return stats


def select_sources(config: AppConfig, only: list[str] | None) -> list[dict[str, Any]]:
    sources = resolve_enabled_sources(config)
    if only:
        wanted = set(only)
        sources = [s for s in sources if s["id"] in wanted]
    return sources


def create_run(conn: Any, trigger: str) -> tuple[int, str]:
    started = _now()
    cur = conn.execute("INSERT INTO runs (started_at, trigger, summary) VALUES (?, ?, '{}')", (started, trigger))
    conn.commit()
    return cur.lastrowid, started


def _finish_run(conn: Any, run_id: int, summary: dict[str, Any]) -> str:
    finished = _now()
    conn.execute("UPDATE runs SET finished_at = ?, summary = ? WHERE id = ?", (finished, json.dumps(summary), run_id))
    conn.commit()
    return finished


def execute_run(
    conn: Any,
    config: AppConfig,
    run_id: int,
    started: str,
    sources: list[dict[str, Any]],
    dry_run: bool,
    update_progress: bool = False,
) -> dict[str, Any]:
    """Fetch sources in parallel, then normalize and store results one source at a time.

    The caller must hold the run lock; it is always released here.
    """
    per_source: dict[str, dict[str, Any]] = {}
    try:
        profile = {**config.profile, "blockedCompanies": config.companies.get("blocked", [])}
        url_to_id = {r["canonical_url"]: r["id"] for r in conn.execute("SELECT id, canonical_url FROM jobs")}
        hash_to_id = {r["dedupe_hash"]: r["id"] for r in conn.execute("SELECT id, dedupe_hash FROM jobs WHERE dedupe_hash IS NOT NULL")}
        seen_urls: set[str] = set()
        seen_hashes: set[str] = set()

        def report(source_id: str, **fields: Any) -> None:
            if update_progress:
                PROGRESS.update_source(source_id, **fields)

        with ThreadPoolExecutor(max_workers=MAX_PARALLEL_FETCHES) as pool:
            futures = {pool.submit(fetch_source, source, config): source for source in sources}
            for future in as_completed(futures):
                source = futures[future]
                result = future.result()
                touch_run_lock(conn)
                stats = {"fetched": 0, "new": 0, "known": 0, "skipped": 0, "error": result.error, "duration_ms": result.duration_ms}

                if not result.error:
                    try:
                        batch = process_batch(conn, result.records, source, profile, seen_urls, seen_hashes, url_to_id, hash_to_id, _now(), dry_run)
                        stats.update(batch)
                    except Exception as exc:  # a bad record must not abort the other sources
                        stats["error"] = f"{type(exc).__name__}: {exc}"

                per_source[source["id"]] = stats
                _record_source_state(conn, source["id"], "error" if stats["error"] else "ok", stats["error"], _now())
                report(source["id"], state="error" if stats["error"] else "ok", **stats)

        finished = _finish_run(conn, run_id, per_source)
        for source_id, s in per_source.items():
            conn.execute(
                "INSERT INTO run_sources (run_id, source_id, fetched, new, errors, duration_ms) VALUES (?, ?, ?, ?, ?, ?)",
                (run_id, source_id, s["fetched"], s["new"], 1 if s.get("error") else 0, s["duration_ms"]),
            )
        conn.commit()
        if update_progress:
            PROGRESS.finish()
        return {
            "status": "ok",
            "run_id": run_id,
            "started_at": started,
            "finished_at": finished,
            "dry_run": dry_run,
            "per_source": per_source,
        }
    except Exception as exc:
        _finish_run(conn, run_id, {"error": f"{type(exc).__name__}: {exc}", "sources": per_source})
        if update_progress:
            PROGRESS.finish(error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        release_run_lock(conn)


def run_fetch(
    config: AppConfig,
    only: list[str] | None = None,
    dry_run: bool = False,
    force: bool = False,
    trigger: str = "cli",
) -> dict[str, Any]:
    """Fetch all enabled sources, normalize, dedupe, store. Returns a summary."""
    conn = open_db()
    try:
        ok, message = acquire_run_lock(conn, force)
        if not ok:
            return {"status": "blocked", "message": message}
        sources = select_sources(config, only)
        run_id, started = create_run(conn, trigger)
        return execute_run(conn, config, run_id, started, sources, dry_run)
    finally:
        conn.close()


def doctor(config: AppConfig, report: bool = False) -> list[dict[str, Any]]:
    """Hit every enabled source once and report pass/fail without storing."""
    sources = resolve_enabled_sources(config)
    rows: list[dict[str, Any]] = []
    for source in sources:
        result = fetch_source(source, config)
        rows.append(
            {
                "id": source["id"],
                "tier": source.get("tier", "B"),
                "kind": source.get("type", "selector"),
                "ok": result.error is None,
                "records": len(result.records),
                "error": result.error,
                "duration_ms": result.duration_ms,
            }
        )
    return rows
