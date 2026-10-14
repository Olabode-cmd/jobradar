from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from ...services import runs_service
from ..deps import Conn
from ..schemas.runs import RunStartIn

router = APIRouter(prefix="/api/runs", tags=["runs"])


@router.post("", status_code=202)
def start_run(body: RunStartIn) -> dict[str, int]:
    return runs_service.start_run(body.sources, body.dry_run)


@router.get("/current")
def current_run() -> dict[str, Any]:
    return runs_service.current_run()


@router.get("")
def run_history(conn: Conn) -> dict[str, Any]:
    return runs_service.run_history(conn)
