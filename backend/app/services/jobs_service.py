"""Triage: browse jobs, change their status, ignore whole companies."""

from __future__ import annotations

import sqlite3
from typing import Any

from ..core.errors import InvalidInputError, NotFoundError
from ..db.repositories import jobs as repo
from ..db.repositories.jobs import JobFilters
from ..domain.contact import is_generic_inbox
from .config_service import block_company


def _with_email_flags(job: dict[str, Any]) -> dict[str, Any]:
    if "emails" in job:
        job["emails"] = [{"address": email, "generic": is_generic_inbox(email)} for email in job["emails"]]
    return job


def list_jobs(conn: sqlite3.Connection, filters: JobFilters) -> dict[str, Any]:
    items, total = repo.list_jobs(conn, filters)
    return {"items": items, "total": total, "counts": repo.status_counts(conn, filters.eligibility)}


def get_job(conn: sqlite3.Connection, job_id: int) -> dict[str, Any]:
    job = repo.get_job(conn, job_id)
    if job is None:
        raise NotFoundError("Job not found")
    return _with_email_flags(job)


def update_job(conn: sqlite3.Connection, job_id: int, status: str | None, notes: str | None) -> dict[str, Any]:
    if not repo.job_exists(conn, job_id):
        raise NotFoundError("Job not found")
    repo.update_job(conn, job_id, status, notes)
    return get_job(conn, job_id)


def bulk_update(conn: sqlite3.Connection, job_ids: list[int], status: str) -> dict[str, int]:
    return {"updated": repo.bulk_update_status(conn, job_ids, status)}


def ignore_company(conn: sqlite3.Connection, job_id: int) -> dict[str, Any]:
    job = repo.get_job(conn, job_id)
    if job is None:
        raise NotFoundError("Job not found")
    key = job["company_key"]
    if not key:
        raise InvalidInputError("This job has no company to ignore")
    block_company(key)
    return {"company_key": key, "ignored": repo.ignore_company_jobs(conn, key)}
