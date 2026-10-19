"""The validated, read-only view of the config the pipeline and CLI run against."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from dotenv import load_dotenv

from . import paths


@dataclass
class AppConfig:
    present: bool = False
    profile: dict[str, Any] = field(default_factory=dict)
    sources: dict[str, Any] = field(default_factory=dict)
    companies: dict[str, Any] = field(default_factory=dict)
    custom_sources: list[dict[str, Any]] = field(default_factory=list)
    preferences: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    @property
    def profile_role(self) -> str | None:
        return self.profile.get("role") or None

    @property
    def contact(self) -> str:
        return str(self.preferences.get("userAgentContact") or "")


# (field, allowed types, nullable)
_PROFILE_CHECKS = [
    ("maxAgeDays", (int,), True),
    ("minSalary", (int, float), True),
    ("remoteOnly", (bool,), False),
    ("openToRelocation", (bool,), False),
    ("targetCountries", (list,), False),
    ("includeKeywords", (list,), False),
    ("excludeKeywords", (list,), False),
    ("rejectedPhrases", (list,), False),
    ("blockedRegions", (list,), False),
    ("timezonesOverlap", (str, list), True),
]


def _validate_profile(profile: dict[str, Any], errors: list[str]) -> None:
    """Type-check profile fields so config mistakes fail with a readable message."""
    for key, allowed, nullable in _PROFILE_CHECKS:
        if key not in profile:
            continue
        value = profile[key]
        if value is None and nullable:
            continue
        if not isinstance(value, allowed):
            expected = " or ".join(t.__name__ for t in allowed) + (" or null" if nullable else "")
            errors.append(f"jobradar.config.json: '{key}' must be {expected}")


def load_config() -> AppConfig:
    load_dotenv(paths.ENV_PATH)
    config = AppConfig()
    if not paths.CONFIG_PATH.exists():
        config.errors.append(f"jobradar.config.json not found (expected at {paths.CONFIG_PATH})")
        return config
    try:
        data = json.loads(paths.CONFIG_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        config.errors.append(f"jobradar.config.json is not valid JSON: {exc}")
        return config

    config.present = True
    config.profile = data.get("profile", {})
    config.sources = data.get("sources", {})
    config.companies = data.get("companies", {})
    config.custom_sources = data.get("customSources", [])
    config.preferences = data.get("preferences", {})
    _validate_profile(config.profile, config.errors)
    return config
