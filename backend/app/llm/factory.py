"""Pick the adapter for the configured provider."""

from __future__ import annotations

from .anthropic import AnthropicClient
from .client import LlmClient, LlmError
from .openai_compatible import OpenAICompatibleClient
from .settings import ANTHROPIC, OPENAI_COMPATIBLE, LlmSettings


def create_client(settings: LlmSettings) -> LlmClient:
    if not settings.enabled:
        raise LlmError("not_configured", "No API key is set. Add one in Settings first.")
    if settings.provider == ANTHROPIC:
        return AnthropicClient(settings)
    if settings.provider == OPENAI_COMPATIBLE:
        return OpenAICompatibleClient(settings)
    raise LlmError("not_configured", f"Unknown LLM provider '{settings.provider}'.")
