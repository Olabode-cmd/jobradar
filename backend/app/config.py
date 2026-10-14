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
    return cfg


def llm_settings() -> dict[str, str | None]:
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