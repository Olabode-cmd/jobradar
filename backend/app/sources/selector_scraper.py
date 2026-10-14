"""Generic selector source driver (Custom Source engine).

Fetches a listing page with Scrapling's HTTP fetcher and extracts records with
CSS selectors from the source config. Phase 5 hardens this: pagination, date
parsing, adaptive selectors, and browser mode for JS-rendered pages.
"""

from __future__ import annotations

from typing import Any

from .http import http_get


def scrape_listing(source: dict[str, Any]) -> list[dict[str, Any]]:
    """Fetch one listing page and return raw records for its item selector."""
    source_id = source.get("id", "custom")
    url = source.get("startUrl")
    item_selector = source.get("itemSelector")
    if not url or not item_selector:
        raise ValueError(f"source '{source_id}' needs 'startUrl' and 'itemSelector'")

    response = http_get(url, source.get("timeout"))
    if response.status >= 400:
        raise RuntimeError(f"HTTP {response.status}")

    records: list[dict[str, Any]] = []
    fields = source.get("fields", {}) or {}
    for item in response.css(item_selector):
        record: dict[str, Any] = {"source": source_id}
        for field_name, selector in fields.items():
            if selector:
                record[field_name] = item.css(selector).get()
        # A link inside the item is the best guess for the apply URL.
        link = item.css("a").get()
        if link is not None and link.attrib.get("href"):
            record.setdefault("url", link.attrib["href"])
        records.append(record)
    return records