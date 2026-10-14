"""Job queries and triage updates for the dashboard."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

STATUSES = ("new", "saved", "applied", "interviewing", "rejected", "ignored")
ELIGIBILITIES = ("eligible", "unclear", "restricted")
SORTS = {
    "score": "j.score DESC, j.posted_at DESC, j.id DESC",
    "recent": "j.posted_at DESC, j.score DESC, j.id DESC",
}
MAX_PAGE_SIZE = 200


@dataclass
class JobFilters:
    status: str | None = "new"
    eligibility: tuple[str, ...] = ("eligible", "unclear")
    query: str | None = None
    source: str | None = None
    remote_only: bool = False
    sort: str = "score"
    limit: int = 50
    offset: int = 0


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _json_value(text: str | None) -> Any:
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _like(text: str) -> str:
    escaped = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def _where(filters: JobFilters) -> tuple[str, list[Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if filters.status:
        clauses.append("j.status = ?")
        params.append(filters.status)
    if filters.eligibility:
        clauses.append(f"j.eligibility IN ({','.join('?' * len(filters.eligibility))})")
        params.extend(filters.eligibility)
    if filters.query:
        clauses.append("(j.title LIKE ? ESCAPE '\\' OR j.company LIKE ? ESCAPE '\\')")
        params.extend([_like(filters.query)] * 2)
    if filters.source:
        clauses.append("j.id IN (SELECT job_id FROM job_sources WHERE source_id = ?)")
        params.append(filters.source)
    if filters.remote_only:
        clauses.append("j.remote_status IS NOT NULL")
    return (" WHERE " + " AND ".join(clauses)) if clauses else "", params


def _summary(row: sqlite3.Row, sources: list[str]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "title": row["title"],
        "company": row["company"],
        "location_text": row["location_text"],
        "remote": row["remote_status"] is not None,
        "posted_at": row["posted_at"],
        "posted_estimated": row["posted_at"] == row["first_seen_at"],
        "first_seen_at": row["first_seen_at"],
        "score": row["score"],
        "eligibility": row["eligibility"],
        "status": row["status"],
        "apply_url": row["apply_url"],
        "apply_method": row["apply_method"],
        "reposted": bool(row["reposted"]),
        "low_confidence": bool(row["low_confidence"]),
        "sources": sources,
    }


def _sources_by_job(conn: sqlite3.Connection, job_ids: list[int]) -> dict[int, list[str]]:
    if not job_ids:
        return {}
    rows = conn.execute(
        f"SELECT DISTINCT job_id, source_id FROM job_sources WHERE job_id IN ({','.join('?' * len(job_ids))})"
        " ORDER BY source_id",
        job_ids,
    ).fetchall()
    grouped: dict[int, list[str]] = {}
    for row in rows:
        grouped.setdefault(row["job_id"], []).append(row["source_id"])
    return grouped


def list_jobs(conn: sqlite3.Connection, filters: JobFilters) -> tuple[list[dict[str, Any]], int]:
    where, params = _where(filters)
    total = conn.execute(f"SELECT COUNT(*) FROM jobs j{where}", params).fetchone()[0]
    order = SORTS.get(filters.sort, SORTS["score"])
    limit = max(1, min(filters.limit, MAX_PAGE_SIZE))
    rows = conn.execute(
        f"SELECT j.* FROM jobs j{where} ORDER BY {order} LIMIT ? OFFSET ?",
        [*params, limit, max(0, filters.offset)],
    ).fetchall()
    sources = _sources_by_job(conn, [row["id"] for row in rows])
    return [_summary(row, sources.get(row["id"], [])) for row in rows], total


def status_counts(conn: sqlite3.Connection) -> dict[str, int]:
    counts = {status: 0 for status in STATUSES}
    for row in conn.execute("SELECT status, COUNT(*) AS n FROM jobs GROUP BY status"):
        counts[row["status"]] = row["n"]
    return counts


def get_job(conn: sqlite3.Connection, job_id: int) -> dict[str, Any] | None:
    row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if row is None:
        return None
    links = conn.execute(
        "SELECT source_id, url, seen_at FROM job_sources WHERE job_id = ? ORDER BY source_id", (job_id,)
    ).fetchall()
    detail = _summary(row, sorted({link["source_id"] for link in links}))
    detail.update(
        {
            "company_key": row["company_key"],
            "description": row["description"],
            "salary_text": row["salary_text"],
            "emails": [str(email) for email in _as_list(_json_value(row["emails"]))],
            "score_reasons": [str(reason) for reason in _as_list(_json_value(row["score_reasons"]))],
            "region_restrictions": _as_list(_json_value(row["region_restrictions"])),
            "llm_result": _json_value(row["llm_result"]),
            "notes": row["notes"],
            "applied_at": row["applied_at"],
            "status_changed_at": row["status_changed_at"],
            "source_links": [dict(link) for link in links],
        }
    )
    return detail


def export_rows(conn: sqlite3.Connection, statuses: tuple[str, ...]) -> list[dict[str, Any]]:
    """Full records for export, newest triage first. An empty `statuses` means every job."""
    where = f" WHERE status IN ({','.join('?' * len(statuses))})" if statuses else ""
    rows = conn.execute(
        f"SELECT id FROM jobs{where} ORDER BY COALESCE(status_changed_at, first_seen_at) DESC, id DESC", statuses
    ).fetchall()
    return [job for job in (get_job(conn, row["id"]) for row in rows) if job is not None]


def job_exists(conn: sqlite3.Connection, job_id: int) -> bool:
    return conn.execute("SELECT 1 FROM jobs WHERE id = ?", (job_id,)).fetchone() is not None


def update_job(conn: sqlite3.Connection, job_id: int, status: str | None, notes: str | None) -> None:
    now = _now()
    if status is not None:
        conn.execute(
            "UPDATE jobs SET status = ?, status_changed_at = ?, reposted = 0,"
            " applied_at = CASE WHEN ? = 'applied' THEN ? ELSE applied_at END WHERE id = ?",
            (status, now, status, now, job_id),
        )
    if notes is not None:
        conn.execute("UPDATE jobs SET notes = ? WHERE id = ?", (notes, job_id))
    conn.commit()


def bulk_update_status(conn: sqlite3.Connection, job_ids: list[int], status: str) -> int:
    if not job_ids:
        return 0
    now = _now()
    cur = conn.execute(
        f"UPDATE jobs SET status = ?, status_changed_at = ?, reposted = 0,"
        f" applied_at = CASE WHEN ? = 'applied' THEN ? ELSE applied_at END"
        f" WHERE id IN ({','.join('?' * len(job_ids))})",
        [status, now, status, now, *job_ids],
    )
    conn.commit()
    return cur.rowcount


def ignore_company_jobs(conn: sqlite3.Connection, company_key: str) -> int:
    cur = conn.execute(
        "UPDATE jobs SET status = 'ignored', status_changed_at = ? WHERE company_key = ? AND status = 'new'",
        (_now(), company_key),
    )
    conn.commit()
    return cur.rowcount
