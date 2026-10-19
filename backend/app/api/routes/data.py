from __future__ import annotations

from fastapi import APIRouter

from ...services import data_service
from ..deps import Conn
from ..schemas.data import ClearDataIn

router = APIRouter(prefix="/api/data", tags=["data"])


@router.post("/clear")
def clear_data(body: ClearDataIn, conn: Conn) -> dict[str, int]:
    return data_service.clear_data(conn, body.keep_triaged)
