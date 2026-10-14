"""LLM configuration. API_KEY is the single optional key."""

from __future__ import annotations

import os
from dataclasses import dataclass

from ..config.env_file import LLM_KEYS, read_env_values

ANTHROPIC = "anthropic"
OPENAI_COMPATIBLE = "openai-compatible"


@dataclass(frozen=True)
class LlmSettings:
    enabled: bool
    provider: str | None = None
    model: str | None = None
    base_url: str | None = None
    api_key: str | None = None


def _current_values() -> dict[str, str]:
    """The environment, with any non-empty value in .env taking precedence.

    Re-read on every call so a hand-edit of .env applies without restarting the server. Empty
    .env lines are ignored, so they never hide a variable exported in the user's shell.
    """
    values = {key: os.environ[key] for key in LLM_KEYS if os.environ.get(key)}
    values.update(read_env_values())
    return values


def load_llm_settings() -> LlmSettings:
    env = _current_values()
    key = env.get("API_KEY")
    if not key:
        return LlmSettings(enabled=False)
    # Anthropic keys start with sk-ant-; everything else is OpenAI-compatible.
    provider = env.get("LLM_PROVIDER") or (ANTHROPIC if key.startswith("sk-ant-") else OPENAI_COMPATIBLE)
    return LlmSettings(
        enabled=True,
        provider=provider,
        model=env.get("LLM_MODEL") or None,
        base_url=env.get("LLM_BASE_URL") or None,
        api_key=key,
    )
