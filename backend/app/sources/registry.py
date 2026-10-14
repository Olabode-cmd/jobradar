"""Which sources exist and which are on: bundled presets, ATS providers and the user's custom sources."""

from __future__ import annotations

from typing import Any

from ..data import load_presets
from .drivers.ats import ats_presets


def _custom_sources(config: Any) -> list[dict[str, Any]]:
    sources = []
    for custom in config.custom_sources:
        name = custom.get("name") or custom.get("id") or "source"
        sources.append(
            {
                "id": f"custom:{name}",
                "name": name,
                "tier": custom.get("tier", "B"),
                "kind": "board",
                "type": "selector",
                "custom": True,
                **custom,
            }
        )
    return sources


def list_all_sources(config: Any) -> list[dict[str, Any]]:
    """Every known source with its resolved `enabled` flag.

    Disabled always wins. Otherwise a source is on if the user opted in (`sources.enabled`)
    or the preset ships on by default. Tier C presets ship off.
    """
    disabled = set(config.sources.get("disabled", []) or [])
    opted_in = set(config.sources.get("enabled", []) or [])
    sources = []
    for source in [*load_presets(), *ats_presets(), *_custom_sources(config)]:
        on_by_default = source.get("defaultEnabled", True)
        enabled = source["id"] not in disabled and (source["id"] in opted_in or on_by_default)
        sources.append({**source, "enabled": enabled})
    return sources


def resolve_enabled_sources(config: Any) -> list[dict[str, Any]]:
    return [source for source in list_all_sources(config) if source["enabled"]]
