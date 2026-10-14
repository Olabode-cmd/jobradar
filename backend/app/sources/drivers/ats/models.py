"""The shape of an ATS provider definition."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class Provider:
    id: str
    name: str
    feed_url: Callable[[str], str]
    parse: Callable[[Any, dict[str, Any]], list[dict[str, Any]]]
    fmt: str  # "json" or "xml"
