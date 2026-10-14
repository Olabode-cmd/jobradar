"""Static, community-maintained data shipped with the repo (JSON files in this directory)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_DIR = Path(__file__).parent


@lru_cache(maxsize=None)
def _load(name: str) -> Any:
    return json.loads((_DIR / name).read_text(encoding="utf-8"))


def load_presets() -> list[dict[str, Any]]:
    return _load("presets.json")


def load_seed_companies() -> list[dict[str, Any]]:
    return _load("seed_companies.json")


def load_phrase_bank() -> dict[str, Any]:
    return _load("phrase_bank.json")


def load_ats_hosts() -> list[str]:
    return _load("ats_hosts.json")
