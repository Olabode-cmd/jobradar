from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from ...services import settings_service
from ..schemas.settings import SettingsUpdateIn

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("")
def get_settings() -> dict[str, Any]:
    return settings_service.get_settings()


@router.post("/test-llm")
def test_llm() -> dict[str, Any]:
    return settings_service.test_llm()


@router.put("")
def update_settings(body: SettingsUpdateIn) -> dict[str, Any]:
    return settings_service.update_settings(body.model_dump())
