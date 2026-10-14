"""Types shared by every source driver."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class FetchContext:
    """What drivers may know about the user's setup, without depending on the config object."""

    contact: str = ""
    tracked_companies: tuple[dict[str, Any], ...] = ()

    @classmethod
    def from_config(cls, config: Any) -> "FetchContext":
        tracked = (config.companies or {}).get("tracked", []) or []
        return cls(
            contact=config.contact,
            tracked_companies=tuple(entry for entry in tracked if isinstance(entry, dict)),
        )


@dataclass
class SourceResult:
    source_id: str
    records: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None
    duration_ms: int = 0
    companies: list[dict[str, Any]] = field(default_factory=list)
