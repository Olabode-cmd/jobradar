"""A real, stealth-patched browser for pages that block plain HTTP (Tier C sources).

One session serves every page a source needs, so Chromium starts once per source. Pages are
loaded logged out, with a pause between them: these sites bot-detect, and many users hit them.
"""

from __future__ import annotations

import random
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any

PAGE_PAUSE_SECONDS = (2.0, 4.0)
DEFAULT_TIMEOUT_SECONDS = 60
INSTALL_HINT = "The browser for this source isn't installed. Run: patchright install chromium"


class BlockedError(RuntimeError):
    """The site answered with a bot challenge or an error page instead of listings."""


def page_text(page: Any) -> str:
    body = page.body
    return body.decode("utf-8", errors="replace") if isinstance(body, bytes) else str(body)


@contextmanager
def browser_session(timeout: int | None = None) -> Iterator[Callable[[str], Any]]:
    """Yield `fetch(url) -> page`. The first call is immediate; later calls wait a few seconds."""
    from scrapling.fetchers import StealthySession

    session = StealthySession(headless=True, network_idle=True, timeout=(timeout or DEFAULT_TIMEOUT_SECONDS) * 1000)
    try:
        session.start()
    except Exception as exc:
        if "Executable doesn't exist" in str(exc):
            raise RuntimeError(INSTALL_HINT) from exc
        raise

    fetched = 0

    def fetch(url: str) -> Any:
        nonlocal fetched
        if fetched:
            time.sleep(random.uniform(*PAGE_PAUSE_SECONDS))
        fetched += 1
        return session.fetch(url)

    try:
        yield fetch
    finally:
        session.close()
