"""Hacker News "Ask HN: Who is hiring?" via the Algolia API.

Comments are free text, so every record is marked low-confidence. The convention
"Company | Role | Location | Remote" in the first line is all we rely on.
"""

from __future__ import annotations

import json
import re
from typing import Any

from ...domain.text import html_to_text
from ..http import http_get
from ..models import FetchContext

SEARCH_URL = (
    "https://hn.algolia.com/api/v1/search_by_date?query=%22Ask%20HN%3A%20Who%20is%20hiring%22"
    "&tags=story,author_whoishiring&hitsPerPage=5"
)
COMMENTS_URL = "https://hn.algolia.com/api/v1/search?tags=comment,story_{story_id}&hitsPerPage=1000&page={page}"
ITEM_URL = "https://news.ycombinator.com/item?id={item_id}"
MAX_PAGES = 4

_ROLE_WORDS = re.compile(
    r"engineer|developer|designer|manager|scientist|analyst|architect|lead|director|"
    r"researcher|specialist|recruiter|writer|devops|sre|product|marketing|sales",
    re.IGNORECASE,
)
_HREF = re.compile(r'href="(https?://[^"]+)"')


def _get_json(url: str, timeout: int | None, ctx: FetchContext) -> Any:
    response = http_get(url, timeout, contact=ctx.contact)
    if response.status >= 400:
        raise RuntimeError(f"HTTP {response.status}")
    return json.loads(response.body)


def _latest_thread_id(timeout: int | None, ctx: FetchContext) -> str:
    for hit in _get_json(SEARCH_URL, timeout, ctx).get("hits", []):
        if str(hit.get("title", "")).lower().startswith("ask hn: who is hiring"):
            return str(hit["objectID"])
    raise RuntimeError("could not find a current 'Who is hiring?' thread")


def parse_comment(comment: dict[str, Any], source_id: str) -> dict[str, Any] | None:
    text = html_to_text(comment.get("comment_text"))
    if not text:
        return None
    header = text.splitlines()[0]
    parts = [part.strip() for part in header.split("|") if part.strip()]
    if len(parts) < 2:
        return None

    role = next((part for part in parts[1:] if _ROLE_WORDS.search(part)), parts[1])
    item_url = ITEM_URL.format(item_id=comment["objectID"])
    links = _HREF.findall(comment.get("comment_text") or "")
    return {
        "source": source_id,
        "title": role[:200],
        "company": parts[0][:120],
        "url": item_url,
        "apply_url": links[0] if links else item_url,
        "location": " | ".join(parts[1:])[:200],
        "description": comment.get("comment_text"),
        "date": comment.get("created_at"),
        "remote": True if "remote" in header.lower() else None,
        "low_confidence": True,
    }


def fetch(source: dict[str, Any], ctx: FetchContext) -> list[dict[str, Any]]:
    timeout = source.get("timeout")
    story_id = _latest_thread_id(timeout, ctx)

    records: list[dict[str, Any]] = []
    for page in range(MAX_PAGES):
        hits = _get_json(COMMENTS_URL.format(story_id=story_id, page=page), timeout, ctx).get("hits", [])
        if not hits:
            break
        for hit in hits:
            if str(hit.get("parent_id")) != story_id:
                continue
            record = parse_comment(hit, source["id"])
            if record:
                records.append(record)
    return records
