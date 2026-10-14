"""LLM configuration from the environment. API_KEY is the single optional key."""

from __future__ import annotations

import os
from dataclasses import dataclass

ANTHROPIC = "anthropic"
OPENAI_COMPATIBLE = "openai-compatible"


@dataclass(frozen=True)
class LlmSettings:
    enabled: bool
    provider: str | None = None
    model: str | None = None
    base_url: str | None = None
    api_key: str | None = None


def load_llm_settings() -> LlmSettings:
    key = os.getenv("API_KEY")
    if not key:
        return LlmSettings(enabled=False)
    # Anthropic keys start with sk-ant-; everything else is OpenAI-compatible.
    provider = os.getenv("LLM_PROVIDER") or (ANTHROPIC if key.startswith("sk-ant-") else OPENAI_COMPATIBLE)
    return LlmSettings(
        enabled=True,
        provider=provider,
        model=os.getenv("LLM_MODEL") or None,
        base_url=os.getenv("LLM_BASE_URL") or None,
        api_key=key,
    )
