"""Dashboard job endpoints: list, detail, triage."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query

from . import jobs_repo
from .config import ConfigFileError, add_blocked_company
from .db import open_db
from .jobs_repo import ELIGIBILITIES, STATUSES, JobFilters
from .schemas import BulkStatusIn, JobUpdateIn

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


def get_conn() -> Iterator[sqlite3.Connection]:
    conn = open_db()
    try:
        yield conn
    finally:
        conn.close()


Conn = Annotated[sqlite3.Connection, Depends(get_conn)]


def _split(value: str | None, allowed: tuple[str, ...], label: str) -> tuple[str, ...]:
    items = tuple(part.strip() for part in (value or "").split(",") if part.strip())
    unknown = [item for item in items if item not in allowed]
    if unknown:
        raise HTTPException(status_code=422, detail=f"Unknown {label}: {', '.join(unknown)}")
    return items


@router.get("")
def list_jobs(
    conn: Conn,
    status: Annotated[str | None, Query(description="One status, or 'all'")] = "new",
    eligibility: str = "eligible,unclear",
    q: Annotated[str | None, Query(max_length=120)] = None,
    source: Annotated[str | None, Query(max_length=120)] = None,
    remote_only: bool = False,
    sort: Literal["score", "recent"] = "score",
    limit: Annotated[int, Query(ge=1, le=jobs_repo.MAX_PAGE_SIZE)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict[str, Any]:
    if status not in (None, "all", *STATUSES):
        raise HTTPException(status_code=422, detail=f"Unknown status: {status}")
    filters = JobFilters(
        status=None if status in (None, "all") else status,
        eligibility=_split(eligibility, ELIGIBILITIES, "eligibility"),
        query=(q or "").strip() or None,
        source=source or None,
        remote_only=remote_only,
        sort=sort,
        limit=limit,
        offset=offset,
    )
    items, total = jobs_repo.list_jobs(conn, filters)
    return {"items": items, "total": total, "counts": jobs_repo.status_counts(conn)}


@router.post("/bulk")
def bulk_update(body: BulkStatusIn, conn: Conn) -> dict[str, int]:
    return {"updated": jobs_repo.bulk_update_status(conn, body.ids, body.status)}


@router.get("/{job_id}")
def get_job(job_id: int, conn: Conn) -> dict[str, Any]:
    job = jobs_repo.get_job(conn, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.patch("/{job_id}")
def update_job(job_id: int, body: JobUpdateIn, conn: Conn) -> dict[str, Any]:
    job = jobs_repo.update_job(conn, job_id, body.status, body.notes)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/{job_id}/ignore-company")
def ignore_company(job_id: int, conn: Conn) -> dict[str, Any]:
    job = jobs_repo.get_job(conn, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    key = job["company_key"]
    if not key:
        raise HTTPException(status_code=422, detail="This job has no company to ignore")
    try:
        add_blocked_company(key)
    except ConfigFileError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"company_key": key, "ignored": jobs_repo.ignore_company_jobs(conn, key)}
