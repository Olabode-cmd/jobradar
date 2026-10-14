"""Source management: list with health, enable or disable, and a no-save test fetch."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from typing import Any

from ..config import AppConfig, load_config, mutate_config
from ..core.errors import NotFoundError
from ..db.repositories import health_state
from ..domain.job import is_usable, normalize_job
from ..sources import FetchContext, fetch_source, list_all_sources
from ..sources.drivers.ats import tracked_for_provider

TIER_C_WARNING = (
    "Logged-out scraping only. This site actively blocks bots, so expect breakage or empty results. "
    "Use at your own risk."
)
TEST_SAMPLE_SIZE = 5


def _find(config: AppConfig, source_id: str) -> dict[str, Any]:
    for source in list_all_sources(config):
        if source["id"] == source_id:
            return source
    raise NotFoundError("Source not found")


def _describe(config: AppConfig, source: dict[str, Any], state: Any) -> dict[str, Any]:
    tracked = None
    if source.get("type") == "ats":
        tracked = len(tracked_for_provider(config.companies.get("tracked", []) or [], source["provider"]))
    return {
        "id": source["id"],
        "name": source.get("name") or source["id"],
        "tier": source.get("tier", "B"),
        "kind": source.get("kind", "board"),
        "type": source.get("type", "selector"),
        "enabled": source["enabled"],
        "custom": bool(source.get("custom")),
        "default_enabled": source.get("defaultEnabled", True),
        "tracked_companies": tracked,
        "warning": TIER_C_WARNING if source.get("tier") == "C" else None,
        "last_run_at": state["last_run_at"] if state else None,
        "last_status": state["last_status"] if state else None,
        "last_error": state["last_error"] if state else None,
        "last_success_at": state["last_success_at"] if state else None,
    }


def list_sources(conn: sqlite3.Connection) -> dict[str, Any]:
    config = load_config()
    states = health_state.source_states(conn)
    return {"items": [_describe(config, source, states.get(source["id"])) for source in list_all_sources(config)]}


def set_enabled(conn: sqlite3.Connection, source_id: str, enabled: bool) -> dict[str, Any]:
    source = _find(load_config(), source_id)
    default_on = source.get("defaultEnabled", True)

    def mutate(document: dict[str, Any]) -> None:
        sources = document["sources"]
        opted_in = [key for key in sources.get("enabled", []) or [] if key != source_id]
        disabled = [key for key in sources.get("disabled", []) or [] if key != source_id]
        if enabled and not default_on:
            opted_in.append(source_id)
        if not enabled and default_on:
            disabled.append(source_id)
        sources["enabled"], sources["disabled"] = opted_in, disabled

    mutate_config(mutate)
    config = load_config()
    return _describe(config, _find(config, source_id), health_state.source_states(conn).get(source_id))


def test_source(source_id: str) -> dict[str, Any]:
    """Fetch once and show the first few parsed jobs without saving anything."""
    config = load_config()
    source = _find(config, source_id)
    result = fetch_source(source, FetchContext.from_config(config))

    now = datetime.now(UTC).isoformat()
    sample = []
    for raw in result.records:
        if not is_usable(raw):
            continue
        job = normalize_job(raw, source, now)
        sample.append(
            {
                "title": job["title"],
                "company": job["company"],
                "location_text": job["location_text"],
                "posted_at": job["posted_at"],
                "url": job["apply_url"],
            }
        )
        if len(sample) == TEST_SAMPLE_SIZE:
            break
    return {
        "ok": result.error is None,
        "error": result.error,
        "count": len(result.records),
        "sample": sample,
        "duration_ms": result.duration_ms,
    }
