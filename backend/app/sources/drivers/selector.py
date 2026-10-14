"""Generic selector source driver (the Custom Source engine).

Fetches a listing page and extracts records with CSS selectors from the source config.
Field selectors can be plain ("h2.title") or carry a Scrapling pseudo-element
("a::attr(href)", "span::text"). Plain selectors yield the element's text, or its
href for the url fields.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urljoin, urlparse

from ..http import http_get
from ..models import FetchContext

URL_FIELDS = ("url", "apply_url")


def _collapse(text: str) -> str:
    return " ".join(text.split())


def _extract(item: Any, selector: str, field_name: str) -> str | None:
    if "::" in selector:
        value = item.css(selector).get()
        return (_collapse(str(value)) or None) if value is not None else None

    matches = item.css(selector)
    if len(matches) == 0:
        return None
    element = matches[0]
    if field_name in URL_FIELDS:
        href = element.attrib.get("href")
        if href:
            return href.strip()
    return _collapse(element.get_all_text(separator=" ", strip=True)) or None


def _item_link(item: Any) -> str | None:
    href = item.attrib.get("href")
    if href:
        return href.strip()
    anchors = item.css("a[href]")
    return anchors[0].attrib["href"].strip() if len(anchors) else None


def _absolute(base: str, href: str) -> str | None:
    joined = urljoin(base, href)
    return joined if urlparse(joined).scheme in ("http", "https") else None


def fetch(source: dict[str, Any], ctx: FetchContext) -> list[dict[str, Any]]:
    source_id = source.get("id", "custom")
    url = source.get("startUrl")
    item_selector = source.get("itemSelector")
    if not url or not item_selector:
        raise ValueError(f"source '{source_id}' needs 'startUrl' and 'itemSelector'")

    response = http_get(url, source.get("timeout"), stealth=True)
    if response.status >= 400:
        raise RuntimeError(f"HTTP {response.status}")

    base_url = str(getattr(response, "url", None) or url)
    fields = source.get("fields", {}) or {}
    records: list[dict[str, Any]] = []

    for item in response.css(item_selector):
        record: dict[str, Any] = {"source": source_id}
        for field_name, selector in fields.items():
            if selector:
                record[field_name] = _extract(item, selector, field_name)

        if not record.get("url"):
            record["url"] = _item_link(item)
        for field_name in URL_FIELDS:
            if record.get(field_name):
                record[field_name] = _absolute(base_url, record[field_name])
        records.append(record)
    return records
