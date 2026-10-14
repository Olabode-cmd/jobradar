"""The provider-agnostic contract every LLM adapter implements."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Protocol


class LlmError(Exception):
    """A failed LLM call. `kind` lets callers tell failures apart without parsing messages."""

    def __init__(self, kind: str, message: str) -> None:
        super().__init__(message)
        self.kind = kind  # "not_configured" | "auth" | "rate_limit" | "not_found" | "bad_request" | "server" | "network" | "unexpected"


@dataclass(frozen=True)
class LlmReply:
    text: str
    model: str | None = None


class LlmClient(Protocol):
    def complete(self, system: str, prompt: str, max_tokens: int = 300) -> LlmReply: ...


# Statuses that abort an LLM pass early: retrying the next job would fail the same way.
FATAL_KINDS = frozenset({"not_configured", "auth", "rate_limit", "not_found", "network"})


def _provider_message(body: Any) -> str:
    """Pull the human message out of an OpenAI- or Anthropic-style error body."""
    try:
        data = json.loads(body) if isinstance(body, (bytes, str)) else body
        error = data.get("error") if isinstance(data, dict) else None
        if isinstance(error, dict) and error.get("message"):
            return str(error["message"])[:300]
        if isinstance(error, str):
            return error[:300]
    except (ValueError, AttributeError):
        pass
    return ""


def raise_for_status(status: int, body: Any, provider: str) -> None:
    """Translate an HTTP failure into an LlmError. The API key is never part of any message."""
    if status < 400:
        return
    detail = _provider_message(body)
    suffix = f" ({detail})" if detail else ""
    if status in (401, 403):
        raise LlmError("auth", f"{provider} rejected the API key{suffix}.")
    if status == 404:
        raise LlmError("not_found", f"{provider} could not find that model or endpoint{suffix}. Check the model name and base URL.")
    if status == 429:
        raise LlmError("rate_limit", f"{provider} is rate limiting this key{suffix}. Try again shortly.")
    if status >= 500:
        raise LlmError("server", f"{provider} had a server error (HTTP {status}){suffix}.")
    raise LlmError("bad_request", f"{provider} rejected the request (HTTP {status}){suffix}.")
