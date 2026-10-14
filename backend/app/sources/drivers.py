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

from .ats import ats_presets, fetch_ats
from .hackernews import fetch_hackernews
from .http import http_get
from .selector_scraper import scrape_listing

PRESETS_PATH = Path(__file__).parent / "presets.json"


@dataclass
class SourceResult:
    source_id: str
    records: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None
    duration_ms: int = 0
    companies: list[dict[str, Any]] = field(default_factory=list)


def load_presets() -> list[dict[str, Any]]:
    return [*json.loads(PRESETS_PATH.read_text(encoding="utf-8")), *ats_presets()]


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


def _first(item: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = item.get(key)
        if value not in (None, "", []):
            return value
    return None


def _salary_text(item: dict[str, Any]) -> str | None:
    text = _first(item, "salary", "salary_text")
    if text:
        return str(text)
    low = _first(item, "salaryMin", "minSalary")
    high = _first(item, "salaryMax", "maxSalary")
    if not low and not high:
        return None
    currency = _first(item, "salaryCurrency", "currency") or ""
    period = _first(item, "salaryPeriod") or ""
    amount = f"{low}–{high}" if low and high else str(low or high)
    return " ".join(part for part in (str(currency), amount, str(period)) if part)


def _remote_flag(source: dict[str, Any], item: dict[str, Any]) -> bool | None:
    if source.get("allRemote"):
        return True
    flag = item.get("remote")
    return flag if isinstance(flag, bool) else None


def _fetch_json(source: dict[str, Any]) -> list[dict[str, Any]]:
    """JSON API boards. Field names vary per board, so each field tries the known spellings."""
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
        url = _first(item, "url", "apply_url", "link", "guid") or ""
        restrictions = item.get("locationRestrictions")
        records.append(
            {
                "source": source["id"],
                "title": _first(item, "position", "title", "name", "jobTitle"),
                "company": _first(item, "company", "company_name", "companyName"),
                "url": url,
                "apply_url": _first(item, "apply_url", "application_url", "applicationLink") or url,
                "location": _first(item, "location", "candidate_required_location", "jobGeo", "city"),
                "description": _first(item, "description", "content", "jobDescription"),
                "salary": _salary_text(item),
                "date": _first(item, "date", "publication_date", "created_at", "pubDate", "pub_date", "publishedAt", "epoch"),
                "tags": item.get("tags"),
                "remote": _remote_flag(source, item),
                "region_restrictions": restrictions if isinstance(restrictions, list) and restrictions else None,
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
                "remote": True if source.get("allRemote") else None,
            }
        )
    return records


def fetch_source(source: dict[str, Any], config: Any) -> SourceResult:
    """Fetch one source and return raw records (or the error). Never raises."""
    source_id = source["id"]
    t0 = time.perf_counter()
    companies: list[dict[str, Any]] = []
    try:
        kind = source.get("type", "selector")
        if kind == "api":
            records = _fetch_json(source)
        elif kind == "rss":
            records = _fetch_rss(source)
        elif kind == "ats":
            records, companies = fetch_ats(source, config)
        elif kind == "hn":
            records = fetch_hackernews(source)
        else:
            records = scrape_listing(source)
        return SourceResult(
            source_id,
            records=records,
            duration_ms=int((time.perf_counter() - t0) * 1000),
            companies=companies,
        )
    except Exception as exc:
        return SourceResult(
            source_id,
            error=f"{type(exc).__name__}: {exc}",
            duration_ms=int((time.perf_counter() - t0) * 1000),
        )
