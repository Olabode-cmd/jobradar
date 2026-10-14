"""The one optional LLM key and its overrides, stored in .env and never echoed back in full."""

from __future__ import annotations

from typing import Any

from ..config.env_file import mask_secret, read_env_values, update_env_values
from ..config.paths import ENV_PATH
from ..core.errors import InvalidInputError
from ..llm import load_llm_settings

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
    }


def update_settings(changes: dict[str, str | None]) -> dict[str, Any]:
    """`changes` uses API field names; None means leave unchanged, "" clears the value."""
    base_url = changes.get("base_url")
    if base_url and not base_url.startswith(("http://", "https://")):
        raise InvalidInputError("Base URL must start with http:// or https://")

    update_env_values({FIELD_TO_ENV[field]: value for field, value in changes.items() if value is not None})
    return get_settings()
