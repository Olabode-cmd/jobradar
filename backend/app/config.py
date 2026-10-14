"""Config loading: jobradar.config.json + .env, both at the repo root."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# backend/app/config.py -> repo root
REPO_ROOT = Path(__file__).resolve().parents[2]

CONFIG_PATH = REPO_ROOT / "jobradar.config.json"


class ConfigFileError(Exception):
    """The config file exists but cannot be read as a JSON object."""


def default_config() -> dict[str, Any]:
    return {
        "profile": {
            "role": "",
            "includeKeywords": [],
            "excludeKeywords": [],
            "rejectedPhrases": [],
            "remoteOnly": True,
            "blockedRegions": [],
            "timezonesOverlap": None,
            "minSalary": None,
            "maxAgeDays": 14,
        },
        "sources": {"disabled": []},
        "companies": {"tracked": []},
        "customSources": [],
        "preferences": {"userAgentContact": ""},
    }


def read_config_document() -> tuple[dict[str, Any], bool]:
    """Return (document merged over defaults, whether the file exists)."""
    document = default_config()
    if not CONFIG_PATH.exists():
        return document, False
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise ConfigFileError(f"jobradar.config.json could not be read: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigFileError("jobradar.config.json must contain a JSON object")
    for key, value in data.items():
        if isinstance(value, dict) and isinstance(document.get(key), dict):
            document[key] = {**document[key], **value}
        else:
            document[key] = value
    return document, True


def write_config_document(document: dict[str, Any]) -> None:
    """Atomic write so a concurrent CLI run never reads a half-written file."""
    tmp_path = CONFIG_PATH.with_suffix(".json.tmp")
    tmp_path.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp_path, CONFIG_PATH)


@dataclass
class AppConfig:
    present: bool = False
    profile: dict[str, Any] = field(default_factory=dict)
    sources: dict[str, Any] = field(default_factory=dict)
    companies: dict[str, Any] = field(default_factory=dict)
    custom_sources: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def profile_role(self) -> str | None:
        return self.profile.get("role") or None


def _validate(profile: dict[str, Any], errors: list[str]) -> None:
    """Type-check the profile fields so config mistakes fail with a readable message."""
    # Each entry: (field, allowed types tuple, nullable)
    checks = [
        ("maxAgeDays", (int,), True),
        ("minSalary", (int, float), True),
        ("remoteOnly", (bool,), False),
        ("includeKeywords", (list,), False),
        ("excludeKeywords", (list,), False),
        ("rejectedPhrases", (list,), False),
        ("blockedRegions", (list,), False),
        ("timezonesOverlap", (str, list), True),
    ]
    for key, allowed, nullable in checks:
        if key not in profile:
            continue
        value = profile[key]
        if value is None and nullable:
            continue
        if not isinstance(value, allowed):
            expected = " or ".join(t.__name__ for t in allowed) + (" or null" if nullable else "")
            errors.append(f"jobradar.config.json: '{key}' must be {expected}")


def load_config() -> AppConfig:
    load_dotenv(REPO_ROOT / ".env")
    cfg = AppConfig()
    if not CONFIG_PATH.exists():
        cfg.errors.append(f"jobradar.config.json not found (expected at {CONFIG_PATH})")
        return cfg
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        cfg.errors.append(f"jobradar.config.json is not valid JSON: {exc}")
        return cfg
    cfg.present = True
    cfg.profile = data.get("profile", {})
    cfg.sources = data.get("sources", {})
    cfg.companies = data.get("companies", {})
    cfg.custom_sources = data.get("customSources", [])
    _validate(cfg.profile, cfg.errors)
    return cfg


def llm_settings() -> dict[str, str | bool | None]:
    """LLM configuration from .env. API_KEY is the single optional key."""
    key = os.getenv("API_KEY")
    if not key:
        return {"enabled": False, "provider": None, "model": None, "base_url": None}
    # Anthropic keys start with sk-ant-; everything else is OpenAI-compatible.
    provider = os.getenv("LLM_PROVIDER") or ("anthropic" if key.startswith("sk-ant-") else "openai-compatible")
    return {
        "enabled": True,
        "provider": provider,
        "model": os.getenv("LLM_MODEL"),
        "base_url": os.getenv("LLM_BASE_URL"),
    }