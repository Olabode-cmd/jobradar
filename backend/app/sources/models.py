"""Types shared by every source driver."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..data import load_countries
from ..domain.profile import target_countries


@dataclass(frozen=True)
class FetchContext:
    """What drivers may know about the user's setup, without depending on the config object.

    Search-driven sources (Indeed, Wellfound, Relocate.me) build every URL from `role` and
    `countries`, so the repo never ships anyone's job title or country list.
    """

    contact: str = ""
    tracked_companies: tuple[dict[str, Any], ...] = ()
    role: str = ""
    max_age_days: int | None = None
    countries: tuple[str, ...] = ()
    open_to_relocation: bool = False

    @classmethod
    def from_config(cls, config: Any) -> "FetchContext":
        tracked = (config.companies or {}).get("tracked", []) or []
        profile = config.profile or {}
        max_age = profile.get("maxAgeDays")
        return cls(
            contact=config.contact,
            tracked_companies=tuple(entry for entry in tracked if isinstance(entry, dict)),
            role=str(profile.get("role") or "").strip(),
            max_age_days=max_age if isinstance(max_age, int) and not isinstance(max_age, bool) else None,
            countries=tuple(target_countries(profile, load_countries())),
            open_to_relocation=profile.get("openToRelocation") is True,
        )


@dataclass
class SourceResult:
    source_id: str
    records: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None
    duration_ms: int = 0
    companies: list[dict[str, Any]] = field(default_factory=list)
