"""The backend's only HTTP entry point: Scrapling's Fetcher.

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
    """One GET through Scrapling's Fetcher. Returns the Response object."""
    from scrapling.fetchers import Fetcher

    kwargs: dict[str, Any] = {"stealthy_headers": stealth}
    if not stealth:
        kwargs["headers"] = {"User-Agent": user_agent(contact)}
    if timeout:
        kwargs["timeout"] = timeout
    return Fetcher.get(url, **kwargs)
