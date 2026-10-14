"""RSS/Atom boards (We Work Remotely), parsed with the standard library."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

from ...net.http import http_get
from ..models import FetchContext


def fetch(source: dict[str, Any], ctx: FetchContext) -> list[dict[str, Any]]:
    response = http_get(source["startUrl"], source.get("timeout"), contact=ctx.contact)
    if response.status >= 400:
        raise RuntimeError(f"HTTP {response.status}")
    body = response.body
    if isinstance(body, bytes):
        body = body.decode("utf-8", errors="replace")
    root = ET.fromstring(body)
    items = root.findall(".//item") or root.findall(".//entry")  # Atom fallback

    records = []
    for item in items:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()

        # We Work Remotely titles look like "Company Name: Job Title"
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
                "description": (item.findtext("description") or item.findtext("summary") or "").strip(),
                "date": (item.findtext("pubDate") or item.findtext("published") or "").strip(),
                "remote": True if source.get("allRemote") else None,
            }
        )
    return records
