"""Writes the pipeline makes while storing fetched jobs."""

from __future__ import annotations

import json
import sqlite3
from datetime import timedelta
from typing import Any

from ...domain.dates import parse_datetime

REPOST_DAYS = 30


def known_urls(conn: sqlite3.Connection) -> dict[str, int]:
    return {row["canonical_url"]: row["id"] for row in conn.execute("SELECT id, canonical_url FROM jobs")}


def known_hashes(conn: sqlite3.Connection) -> dict[str, int]:
    rows = conn.execute("SELECT id, dedupe_hash FROM jobs WHERE dedupe_hash IS NOT NULL")
    return {row["dedupe_hash"]: row["id"] for row in rows}


def attach_source(conn: sqlite3.Connection, job_id: int, source_id: str, url: str, now: str) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO job_sources (job_id, source_id, url, seen_at) VALUES (?, ?, ?, ?)",
        (job_id, source_id, url, now),
    )


def reopen_if_reposted(conn: sqlite3.Connection, job_id: int, posted_at: str | None, now: str) -> None:
    """A duplicate arriving with a much newer posted date re-opens as New."""
    if not posted_at:
        return
    row = conn.execute(
        "SELECT status, status_changed_at, first_seen_at FROM jobs WHERE id = ?", (job_id,)
    ).fetchone()
    if row is None or row["status"] == "new":
        return
    posted = parse_datetime(posted_at)
    changed = parse_datetime(row["status_changed_at"] or row["first_seen_at"] or now)
    if posted is None or changed is None:
        return
    if posted > changed + timedelta(days=REPOST_DAYS):
        conn.execute(
            "UPDATE jobs SET status = 'new', reposted = 1, status_changed_at = ? WHERE id = ?",
            (now, job_id),
        )


def insert_job(conn: sqlite3.Connection, job: dict[str, Any], now: str) -> int:
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
