from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from ...services import config_service
from ..schemas.config import ConfigUpdateIn

router = APIRouter(prefix="/api/config", tags=["config"])


@router.get("")
def get_config() -> dict[str, Any]:
    return config_service.get_config()


@router.put("")
def update_config(update: ConfigUpdateIn) -> dict[str, Any]:
    # Optional profile fields are written only when sent, so an older dashboard can't reset them.
    profile = update.profile.model_dump(exclude_unset=True)
    return config_service.update_config(profile, update.preferences.model_dump())
