"""The backend's only HTTP entry point: Scrapling's Fetcher.

Everything this package fetches goes through here — JSON APIs, RSS feeds, and
HTML pages. DynamicFetcher/StealthyFetcher (browser) join for JS-rendered and
defended pages in Phase 5.
"""

from __future__ import annotations

from typing import Any


def http_get(url: str, timeout: int | None = None) -> Any:
    """One GET through Scrapling's Fetcher. Returns the Response object."""
    from scrapling.fetchers import Fetcher

    kwargs: dict[str, Any] = {"stealthy_headers": True}
    if timeout:
        kwargs["timeout"] = timeout
    return Fetcher.get(url, **kwargs)