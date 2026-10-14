"""The backend's only HTTP client: Scrapling's Fetcher.

Official feeds are fetched with an honest User-Agent (plus the contact string from the
config, so a site can reach the user). Scraped HTML pages use browser-like headers.
DynamicFetcher/StealthyFetcher (a real browser) join for JS-rendered pages in Phase 5.
"""

from __future__ import annotations

from typing import Any

from .. import __version__


def user_agent(contact: str = "") -> str:
    return f"JobRadar/{__version__} (+{contact})" if contact else f"JobRadar/{__version__}"


def http_get(url: str, timeout: int | None = None, *, contact: str = "", stealth: bool = False) -> Any:
    """One GET. Returns the Response object (non-2xx statuses are returned, not raised)."""
    from scrapling.fetchers import Fetcher

    kwargs: dict[str, Any] = {"stealthy_headers": stealth}
    if not stealth:
        kwargs["headers"] = {"User-Agent": user_agent(contact)}
    if timeout:
        kwargs["timeout"] = timeout
    return Fetcher.get(url, **kwargs)


def http_post_json(url: str, payload: dict[str, Any], *, headers: dict[str, str], timeout: int = 30) -> Any:
    """One JSON POST. Returns the Response object (non-2xx statuses are returned, not raised)."""
    from scrapling.fetchers import Fetcher

    # One attempt only: a test button or an AI pass shouldn't sit through Scrapling's default 3 retries.
    return Fetcher.post(url, json=payload, headers=headers, timeout=timeout, retries=1, stealthy_headers=False)
