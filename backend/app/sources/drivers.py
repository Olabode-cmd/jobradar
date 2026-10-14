"""Source drivers — the only place in the backend that touches the network.

Every fetch goes through Scrapling:

- ``Fetcher`` (TLS-impersonated HTTP) for official JSON/RSS feeds and static HTML.
- ``DynamicFetcher`` / ``StealthyFetcher`` (real Chromium) for JS-rendered and
  defended pages — added per source in Phase 5.

Nothing else in the codebase does HTTP. godspeed is the UI's client (browser →
API); Scrapling owns server-side fetching.
"""

from __future__ import annotations

import json
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .http import http_get
from .selector_scraper import scrape_listing

PRESETS_PATH = Path(__file__).parent / "presets.json"


@dataclass
class SourceResult:
    source_id: str
    records: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None
    duration_ms: int = 0


def load_presets() -> list[dict[str, Any]]:
    return json.loads(PRESETS_PATH.read_text(encoding="utf-8"))


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
    """Every known source (presets and custom) with its resolved `enabled` flag.

    Disabled always wins. Otherwise a source is on if the user opted in (`sources.enabled`)
    or the preset ships on by default — Tier C presets ship off.
    """
    disabled = set(config.sources.get("disabled", []) or [])
    opted_in = set(config.sources.get("enabled", []) or [])
    sources = []
    for source in [*load_presets(), *_custom_sources(config)]:
        on_by_default = source.get("defaultEnabled", True)
        enabled = source["id"] not in disabled and (source["id"] in opted_in or on_by_default)
        sources.append({**source, "enabled": enabled})
    return sources


def resolve_enabled_sources(config: Any) -> list[dict[str, Any]]:
    return [source for source in list_all_sources(config) if source["enabled"]]


def _http_get(url: str, timeout: int | None = None) -> Any:
    """One GET through Scrapling's Fetcher. Returns the Response object."""
    return http_get(url, timeout=timeout)


def _fetch_json(source: dict[str, Any]) -> list[dict[str, Any]]:
    """JSON API source: RemoteOK (array), Remotive ({jobs: [...]}), etc."""
    response = _http_get(source["startUrl"], source.get("timeout"))
    if response.status >= 400:
        raise RuntimeError(f"HTTP {response.status}")
    data = response.json()
    if isinstance(data, dict):
        jobs = data.get("jobs") or data.get("data") or []
        if isinstance(jobs, dict):
            jobs = list(jobs.values())
    else:
        jobs = data
    if not isinstance(jobs, list):
        raise RuntimeError(f"unexpected JSON shape from {source['id']}: {type(jobs).__name__}")

    records = []
    for item in jobs:
        if not isinstance(item, dict):
            continue
        url = item.get("url") or item.get("apply_url") or item.get("link") or ""
        records.append(
            {
                "source": source["id"],
                "title": item.get("position") or item.get("title") or item.get("name"),
                "company": item.get("company") or item.get("company_name"),
                "url": url,
                "apply_url": item.get("apply_url") or item.get("application_url") or url,
                "location": item.get("location") or item.get("candidate_required_location") or item.get("city"),
                "description": item.get("description") or item.get("content"),
                "salary": item.get("salary") or item.get("salary_text"),
                "date": item.get("date") or item.get("publication_date") or item.get("created_at"),
                "tags": item.get("tags"),
                "remote": item.get("remote") or ("remote" in str(item.get("job_type", "")).lower()),
            }
        )
    return records


def _fetch_rss(source: dict[str, Any]) -> list[dict[str, Any]]:
    """RSS/Atom source (We Work Remotely, etc.) parsed with the stdlib."""
    response = _http_get(source["startUrl"], source.get("timeout"))
    if response.status >= 400:
        raise RuntimeError(f"HTTP {response.status}")
    body = response.body
    if isinstance(body, bytes):
        body = body.decode("utf-8", errors="replace")
    root = ET.fromstring(body)
    items = root.findall(".//item")
    if not items:
        items = root.findall(".//entry")  # Atom fallback

    records = []
    for item in items:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        description = (item.findtext("description") or item.findtext("summary") or "").strip()
        pub_date = (item.findtext("pubDate") or item.findtext("published") or "").strip()

        # We Work Remotely titles look like "Company Name: Job Title" — split it.
        company = None
        if ":" in title:
            company, _, title = title.partition(":")
            company, title = company.strip(), title.strip()

        records.append(
            {
                "source": source["id"],
                "title": title,
                "company": company,
                "url": link,
                "apply_url": link,
                "description": description,
                "date": pub_date,
            }
        )
    return records


def fetch_source(source: dict[str, Any], config: Any) -> SourceResult:
    """Fetch one source and return raw records (or the error). Never raises."""
    source_id = source["id"]
    t0 = time.perf_counter()
    try:
        kind = source.get("type", "selector")
        if kind == "api":
            records = _fetch_json(source)
        elif kind == "rss":
            records = _fetch_rss(source)
        else:
            records = scrape_listing(source)
        return SourceResult(source_id, records=records, duration_ms=int((time.perf_counter() - t0) * 1000))
    except Exception as exc:
        return SourceResult(
            source_id,
            error=f"{type(exc).__name__}: {exc}",
            duration_ms=int((time.perf_counter() - t0) * 1000),
        )