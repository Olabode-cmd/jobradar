"""Fetch every tracked company's board for one provider."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Iterable

from ....net.http import http_get
from ...models import FetchContext
from .detect import SLUG_RE
from .providers import PROVIDERS
from .models import Provider

COMPANY_FETCH_WORKERS = 4
MAX_RECORDS_PER_BOARD = 1000


def tracked_for_provider(entries: Iterable[Any], provider_id: str) -> list[dict[str, Any]]:
    """Valid, enabled tracked companies for a provider, with names defaulted from the slug."""
    valid = []
    for entry in entries:
        if not isinstance(entry, dict) or entry.get("provider") != provider_id or entry.get("enabled") is False:
            continue
        slug = str(entry.get("slug") or "")
        if SLUG_RE.match(slug):
            valid.append({"name": str(entry.get("name") or slug), "slug": slug, "provider": provider_id})
    return valid


def _load_payload(provider: Provider, slug: str, timeout: int | None, contact: str) -> Any:
    response = http_get(provider.feed_url(slug), timeout, contact=contact)
    if response.status == 404:
        raise RuntimeError("board not found (check the company's slug)")
    if response.status >= 400:
        raise RuntimeError(f"HTTP {response.status}")
    if provider.fmt == "json":
        return response.json()
    body = response.body
    return ET.fromstring(body.decode("utf-8", errors="replace") if isinstance(body, bytes) else body)


def fetch_company(provider: Provider, company: dict[str, Any], timeout: int | None, contact: str = "") -> dict[str, Any]:
    """One board. Never raises: failures come back as `error` so one bad board can't sink the rest."""
    try:
        payload = _load_payload(provider, company["slug"], timeout, contact)
        records = provider.parse(payload, company)[:MAX_RECORDS_PER_BOARD]
        return {"company": company, "records": records, "error": None}
    except Exception as exc:
        return {"company": company, "records": [], "error": f"{type(exc).__name__}: {exc}"}


def fetch(source: dict[str, Any], ctx: FetchContext) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Returns (records, per-company results). Raises only if every board failed."""
    provider = PROVIDERS[source["provider"]]
    companies = tracked_for_provider(ctx.tracked_companies, provider.id)
    if not companies:
        return [], []

    timeout = source.get("timeout")
    with ThreadPoolExecutor(max_workers=COMPANY_FETCH_WORKERS) as pool:
        results = list(pool.map(lambda company: fetch_company(provider, company, timeout, ctx.contact), companies))

    records = [{**record, "source": source["id"]} for result in results for record in result["records"]]
    company_results = [
        {
            "key": f"{provider.id}:{result['company']['slug']}",
            "open_roles": len(result["records"]),
            "error": result["error"],
        }
        for result in results
    ]
    if all(result["error"] for result in results):
        raise RuntimeError(f"all {len(results)} boards failed; first error: {results[0]['error']}")
    return records, company_results
