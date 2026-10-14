"""Minimal generic selector source driver (Custom Source engine, Phase-0 spike).

Proves the core design: a source config (start URL + selectors) flows through
Scrapling's fetcher and parser into raw records. Phase 1 hardens this with
pagination, date parsing, timeouts, and per-source politeness via Scrapling's
spider framework (AutoThrottle, robots.txt).
"""

from __future__ import annotations

from typing import Any


def scrape_listing(source: dict[str, Any]) -> list[dict[str, Any]]:
    """Fetch one source and return raw records for its item selector."""
    from scrapling.fetchers import Fetcher

    source_id = source.get("id", "custom")
    url = source.get("startUrl")
    item_selector = source.get("itemSelector")
    if not url or not item_selector:
        raise ValueError(f"source '{source_id}' needs 'startUrl' and 'itemSelector'")

    page = Fetcher.get(url, stealthy_headers=True)
    records: list[dict[str, Any]] = []
    fields = source.get("fields", {}) or {}
    for item in page.css(item_selector):
        record: dict[str, Any] = {"source_id": source_id}
        for field_name, selector in fields.items():
            if selector:
                record[field_name] = item.css(selector).get()
        records.append(record)
    return records