from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from ...services import sources_service
from ..deps import Conn
from ..schemas.sources import ToggleIn

router = APIRouter(prefix="/api/sources", tags=["sources"])


@router.get("")
def list_sources(conn: Conn) -> dict[str, Any]:
    return sources_service.list_sources(conn)


@router.put("/{source_id}")
def set_enabled(source_id: str, body: ToggleIn, conn: Conn) -> dict[str, Any]:
    return sources_service.set_enabled(conn, source_id, body.enabled)


@router.post("/{source_id}/test")
def test_source(source_id: str) -> dict[str, Any]:
    return sources_service.test_source(source_id)
