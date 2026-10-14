"""Reading and writing the raw jobradar.config.json document."""

from __future__ import annotations

import json
import os
from typing import Any, Callable

from ..core.errors import ConflictError
from . import paths


class ConfigFileError(ConflictError):
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
        "companies": {"tracked": [], "blocked": []},
        "customSources": [],
        "preferences": {"userAgentContact": ""},
    }


def read_config_document() -> tuple[dict[str, Any], bool]:
    """Return (document merged over defaults, whether the file exists)."""
    document = default_config()
    if not paths.CONFIG_PATH.exists():
        return document, False
    try:
        data = json.loads(paths.CONFIG_PATH.read_text(encoding="utf-8"))
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
    tmp_path = paths.CONFIG_PATH.with_suffix(".json.tmp")
    tmp_path.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp_path, paths.CONFIG_PATH)


def mutate_config(mutator: Callable[[dict[str, Any]], None]) -> dict[str, Any]:
    """Read the document, apply `mutator` in place, write it back, return it."""
    document, _ = read_config_document()
    mutator(document)
    write_config_document(document)
    return document
