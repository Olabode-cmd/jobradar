from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from ...services import health_service

router = APIRouter(tags=["health"])


@router.get("/api/health")
def health() -> dict[str, Any]:
    return health_service.health_report()
