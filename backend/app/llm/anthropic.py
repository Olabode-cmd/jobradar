"""Anthropic Messages API adapter."""

from __future__ import annotations

import json

from ..net.http import http_post_json
from .client import LlmError, LlmReply, raise_for_status
from .settings import LlmSettings

DEFAULT_BASE_URL = "https://api.anthropic.com"
DEFAULT_MODEL = "claude-haiku-4-5"
API_VERSION = "2023-06-01"
TIMEOUT_S = 60


class AnthropicClient:
    def __init__(self, settings: LlmSettings) -> None:
        self._key = settings.api_key or ""
        self._model = settings.model or DEFAULT_MODEL
        self._url = f"{(settings.base_url or DEFAULT_BASE_URL).rstrip('/')}/v1/messages"

    def complete(self, system: str, prompt: str, max_tokens: int = 300) -> LlmReply:
        payload = {
            "model": self._model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": prompt}],
        }
        headers = {"x-api-key": self._key, "anthropic-version": API_VERSION, "content-type": "application/json"}
        try:
            response = http_post_json(self._url, payload, headers=headers, timeout=TIMEOUT_S)
        except Exception as exc:
            raise LlmError("network", f"Could not reach Anthropic: {type(exc).__name__}.") from None

        raise_for_status(response.status, response.body, "Anthropic")
        try:
            data = json.loads(response.body)
            text = "".join(block.get("text", "") for block in data["content"] if block.get("type") == "text")
        except (ValueError, KeyError, TypeError, AttributeError):
            raise LlmError("unexpected", "Anthropic returned a response in an unexpected shape.") from None
        return LlmReply(text=text.strip(), model=data.get("model") or self._model)
