from __future__ import annotations

from typing import Annotated, Any, Literal

from fastapi import APIRouter, Query

from ...core.errors import InvalidInputError
from ...db.repositories.jobs import ELIGIBILITIES, MAX_PAGE_SIZE, STATUSES, JobFilters
from ...services import jobs_service
from ..deps import Conn
from ..schemas.jobs import BulkStatusIn, JobUpdateIn

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


def _split(value: str, allowed: tuple[str, ...], label: str) -> tuple[str, ...]:
    items = tuple(part.strip() for part in value.split(",") if part.strip())
    unknown = [item for item in items if item not in allowed]
    if unknown:
        raise InvalidInputError(f"Unknown {label}: {', '.join(unknown)}")
    return items


@router.get("")
def list_jobs(
    conn: Conn,
    status: Annotated[str, Query(description="One status, or 'all'")] = "new",
    eligibility: str = "eligible,unclear",
    q: Annotated[str | None, Query(max_length=120)] = None,
    source: Annotated[str | None, Query(max_length=120)] = None,
    remote_only: bool = False,
    sort: Literal["score", "recent"] = "score",
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict[str, Any]:
    if status != "all" and status not in STATUSES:
        raise InvalidInputError(f"Unknown status: {status}")
    filters = JobFilters(
        status=None if status == "all" else status,
        eligibility=_split(eligibility, ELIGIBILITIES, "eligibility"),
        query=(q or "").strip() or None,
        source=source or None,
        remote_only=remote_only,
        sort=sort,
        limit=limit,
        offset=offset,
    )
    return jobs_service.list_jobs(conn, filters)


@router.post("/bulk")
def bulk_update(body: BulkStatusIn, conn: Conn) -> dict[str, int]:
    return jobs_service.bulk_update(conn, body.ids, body.status)


@router.get("/{job_id}")
def get_job(job_id: int, conn: Conn) -> dict[str, Any]:
    return jobs_service.get_job(conn, job_id)


@router.patch("/{job_id}")
def update_job(job_id: int, body: JobUpdateIn, conn: Conn) -> dict[str, Any]:
    return jobs_service.update_job(conn, job_id, body.status, body.notes)


@router.post("/{job_id}/ignore-company")
def ignore_company(job_id: int, conn: Conn) -> dict[str, Any]:
    return jobs_service.ignore_company(conn, job_id)
