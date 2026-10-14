"""Tracked ATS boards: list with health, add by URL, bulk import, seed list, toggle, remove."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from typing import Any

from ..config import load_config, mutate_config
from ..core.errors import InvalidInputError, NotFoundError
from ..data import load_seed_companies
from ..db.repositories import health_state
from ..sources.drivers.ats import PROVIDERS, detect_company, fetch_company

UNSUPPORTED_URL = (
    "That address isn't a supported careers page. Paste a Greenhouse, Lever, Ashby, Workable, "
    "Recruitee, SmartRecruiters, Teamtailor, Personio, BambooHR or Breezy job board link."
)


def _key(provider: str, slug: str) -> str:
    return f"{provider}:{slug}"


def _title_from_slug(slug: str) -> str:
    return slug.replace("-", " ").replace("_", " ").title()


def _tracked_entries() -> list[dict[str, Any]]:
    entries = (load_config().companies or {}).get("tracked", []) or []
    return [
        entry for entry in entries
        if isinstance(entry, dict) and entry.get("provider") in PROVIDERS and isinstance(entry.get("slug"), str)
    ]


def _matches(entry: Any, provider: str, slug: str) -> bool:
    return isinstance(entry, dict) and entry.get("provider") == provider and str(entry.get("slug", "")).lower() == slug.lower()


def _describe(entry: dict[str, Any], state: Any) -> dict[str, Any]:
    provider = entry["provider"]
    return {
        "provider": provider,
        "provider_name": PROVIDERS[provider].name,
        "slug": entry["slug"],
        "name": str(entry.get("name") or entry["slug"]),
        "enabled": entry.get("enabled") is not False,
        "last_checked_at": state["last_checked_at"] if state else None,
        "last_error": state["last_error"] if state else None,
        "open_roles": state["open_roles"] if state else None,
    }


def _add_entries(new_entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Append entries that aren't tracked yet. Returns the ones actually added."""
    added: list[dict[str, Any]] = []

    def mutate(document: dict[str, Any]) -> None:
        tracked = document["companies"].setdefault("tracked", [])
        known = {
            _key(entry.get("provider", ""), str(entry.get("slug", "")).lower())
            for entry in tracked if isinstance(entry, dict)
        }
        for entry in new_entries:
            key = _key(entry["provider"], entry["slug"].lower())
            if key not in known:
                known.add(key)
                tracked.append(entry)
                added.append(entry)

    mutate_config(mutate)
    return added


def list_companies(conn: sqlite3.Connection) -> dict[str, Any]:
    states = health_state.company_states(conn)
    items = [_describe(entry, states.get(_key(entry["provider"], entry["slug"]))) for entry in _tracked_entries()]
    return {"items": items, "providers": [{"id": p.id, "name": p.name} for p in PROVIDERS.values()]}


def add_company(conn: sqlite3.Connection, url: str) -> dict[str, Any]:
    detected = detect_company(url)
    if detected is None:
        raise InvalidInputError(UNSUPPORTED_URL)
    provider, slug = detected
    probe = fetch_company(PROVIDERS[provider], {"name": _title_from_slug(slug), "slug": slug, "provider": provider}, 20)
    if probe["error"]:
        raise InvalidInputError(f"Couldn't read the {PROVIDERS[provider].name} board '{slug}': {probe['error']}")

    name = probe["records"][0]["company"] if probe["records"] else _title_from_slug(slug)
    _add_entries([{"name": name, "provider": provider, "slug": slug}])
    health_state.record_companies(
        conn,
        [{"key": _key(provider, slug), "open_roles": len(probe["records"]), "error": None}],
        datetime.now(UTC).isoformat(),
    )
    entry = next(e for e in _tracked_entries() if _matches(e, provider, slug))
    return _describe(entry, health_state.company_states(conn).get(_key(entry["provider"], entry["slug"])))



def import_companies(urls: list[str]) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    rejected: list[dict[str, str]] = []
    for line in urls:
        url = line.strip()
        if not url:
            continue
        detected = detect_company(url)
        if detected is None:
            rejected.append({"url": url, "reason": "Not a supported careers page"})
            continue
        provider, slug = detected
        entries.append({"name": _title_from_slug(slug), "provider": provider, "slug": slug})
    added = _add_entries(entries)
    return {"added": len(added), "already_tracked": len(entries) - len(added), "rejected": rejected}


def add_seed_companies() -> dict[str, int]:
    seed = load_seed_companies()
    return {"added": len(_add_entries([dict(entry) for entry in seed])), "available": len(seed)}


def set_enabled(conn: sqlite3.Connection, provider: str, slug: str, enabled: bool) -> dict[str, Any]:
    found = False

    def mutate(document: dict[str, Any]) -> None:
        nonlocal found
        for entry in document["companies"].get("tracked", []):
            if _matches(entry, provider, slug):
                entry["enabled"] = enabled
                found = True

    mutate_config(mutate)
    if not found:
        raise NotFoundError("Company not tracked")
    entry = next(e for e in _tracked_entries() if _matches(e, provider, slug))
    return _describe(entry, health_state.company_states(conn).get(_key(provider, entry["slug"])))


def remove(provider: str, slug: str) -> None:
    removed = False

    def mutate(document: dict[str, Any]) -> None:
        nonlocal removed
        tracked = document["companies"].get("tracked", [])
        kept = [entry for entry in tracked if not _matches(entry, provider, slug)]
        removed = len(kept) != len(tracked)
        document["companies"]["tracked"] = kept

    mutate_config(mutate)
    if not removed:
        raise NotFoundError("Company not tracked")
