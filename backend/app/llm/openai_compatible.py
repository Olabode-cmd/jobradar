"""OpenAI-compatible chat completions adapter (OpenAI, OpenRouter, Groq, Ollama, LM Studio, ...)."""

from __future__ import annotations

import json

from ..net.http import http_post_json
from .client import LlmError, LlmReply, raise_for_status
from .settings import LlmSettings

DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-4o-mini"
TIMEOUT_S = 60


class OpenAICompatibleClient:
    def __init__(self, settings: LlmSettings) -> None:
        self._key = settings.api_key or ""
        self._model = settings.model or DEFAULT_MODEL
        self._url = f"{(settings.base_url or DEFAULT_BASE_URL).rstrip('/')}/chat/completions"
        self._provider = "the LLM provider"

    def complete(self, system: str, prompt: str, max_tokens: int = 300) -> LlmReply:
        payload = {
            "model": self._model,
            "max_tokens": max_tokens,
            "temperature": 0,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        }
        headers = {"Authorization": f"Bearer {self._key}", "Content-Type": "application/json"}
        try:
            response = http_post_json(self._url, payload, headers=headers, timeout=TIMEOUT_S)
        except Exception as exc:
            raise LlmError("network", f"Could not reach {self._provider}: {type(exc).__name__}.") from None

        raise_for_status(response.status, response.body, self._provider)
        try:
            data = json.loads(response.body)
            text = data["choices"][0]["message"]["content"] or ""
        except (ValueError, KeyError, IndexError, TypeError):
            raise LlmError("unexpected", f"{self._provider} returned a response in an unexpected shape.") from None
        return LlmReply(text=str(text).strip(), model=data.get("model") or self._model)
