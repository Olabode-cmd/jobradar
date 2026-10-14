from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query, Response

from ...services import export_service
from ..deps import Conn

router = APIRouter(prefix="/api/export", tags=["export"])


@router.get("")
def export_jobs(
    conn: Conn,
    format: Annotated[str, Query(max_length=20)] = "csv",
    status: Annotated[str, Query(description="Comma-separated statuses; empty means all")] = "",
) -> Response:
    statuses = tuple(part.strip() for part in status.split(",") if part.strip())
    body, media_type, filename = export_service.export_jobs(conn, format, statuses)
    return Response(
        content=body,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
