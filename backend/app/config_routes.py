"""Read and update jobradar.config.json from the dashboard."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from .config import ConfigFileError, read_config_document, write_config_document
from .schemas import ConfigUpdateIn

router = APIRouter(prefix="/api/config", tags=["config"])


def _read_or_conflict() -> tuple[dict[str, Any], bool]:
    try:
        return read_config_document()
    except ConfigFileError as exc:
        # 409 so the UI refuses to edit rather than overwrite a hand-edited file it can't parse
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("")
def get_config() -> dict[str, Any]:
    document, exists = _read_or_conflict()
    return {"exists": exists, "config": document}


@router.put("")
def update_config(update: ConfigUpdateIn) -> dict[str, Any]:
    document, _ = _read_or_conflict()
    # Merge so keys the dashboard doesn't own (sources, companies, unknown extras) survive.
    document["profile"] = {**document.get("profile", {}), **update.profile.model_dump()}
    document["preferences"] = {**document.get("preferences", {}), **update.preferences.model_dump()}
    try:
        write_config_document(document)
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Could not write config file: {exc}") from exc
    return {"exists": True, "config": document}
