"""The one optional LLM key and its overrides, stored in .env and never echoed back in full."""

from __future__ import annotations

import time
from typing import Any

from ..config.env_file import mask_secret, read_env_values, update_env_values
from ..config.paths import CONFIG_PATH, ENV_PATH
from ..core.errors import InvalidInputError
from ..db import default_db_path
from ..llm import LlmError, create_client, load_llm_settings

FIELD_TO_ENV = {
    "api_key": "API_KEY",
    "provider": "LLM_PROVIDER",
    "model": "LLM_MODEL",
    "base_url": "LLM_BASE_URL",
}


def get_settings() -> dict[str, Any]:
    env = read_env_values()
    key = env.get("API_KEY")
    llm = load_llm_settings()
    return {
        "env_file_exists": ENV_PATH.exists(),
        "api_key_set": bool(key),
        "api_key_hint": mask_secret(key) if key else None,
        "provider": env.get("LLM_PROVIDER", ""),
        "detected_provider": llm.provider,
        "model": env.get("LLM_MODEL", ""),
        "base_url": env.get("LLM_BASE_URL", ""),
        "llm_enabled": llm.enabled,
        "db_path": str(default_db_path()),
        "config_path": str(CONFIG_PATH),
    }


def test_llm() -> dict[str, Any]:
    """Send one tiny request with the saved settings. A provider failure is a result, not an error."""
    settings = load_llm_settings()
    started = time.perf_counter()
    try:
        reply = create_client(settings).complete("Reply with the single word OK.", "ping", max_tokens=10)
    except LlmError as exc:
        return {"ok": False, "kind": exc.kind, "message": str(exc), "provider": settings.provider}
    return {
        "ok": True,
        "provider": settings.provider,
        "model": reply.model,
        "reply": reply.text[:80],
        "duration_ms": int((time.perf_counter() - started) * 1000),
    }


def update_settings(changes: dict[str, str | None]) -> dict[str, Any]:
    """`changes` uses API field names; None means leave unchanged, "" clears the value."""
    base_url = changes.get("base_url")
    if base_url and not base_url.startswith(("http://", "https://")):
        raise InvalidInputError("Base URL must start with http:// or https://")

    update_env_values({FIELD_TO_ENV[field]: value for field, value in changes.items() if value is not None})
    return get_settings()
