"""Contact and apply-method extraction from posting text."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from ..data import load_ats_hosts

MAX_EMAILS = 5
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
_NOT_AN_ADDRESS = re.compile(r"\.(png|jpe?g|gif|svg|webp)$", re.IGNORECASE)
_NO_REPLY = re.compile(r"no-?reply|do-?not-?reply|donotreply", re.IGNORECASE)
_GENERIC_LOCAL_PARTS = frozenset(
    {"jobs", "job", "careers", "career", "hr", "hiring", "recruiting", "recruitment",
     "talent", "apply", "info", "contact", "hello", "team", "people", "work", "join"}
)


def extract_emails(value: Any) -> list[str]:
    """Distinct, lower-cased addresses found in text or HTML (mailto links included)."""
    if not value:
        return []
    seen: dict[str, None] = {}
    for match in _EMAIL_RE.findall(str(value)):
        address = match.lower().strip(".")
        if _NOT_AN_ADDRESS.search(address) or _NO_REPLY.search(address):
            continue
        seen.setdefault(address)
    return list(seen)[:MAX_EMAILS]


def is_generic_inbox(address: str) -> bool:
    return address.split("@", 1)[0] in _GENERIC_LOCAL_PARTS


def _host_matches(host: str, suffixes: list[str]) -> bool:
    return any(host == suffix or host.endswith(f".{suffix}") for suffix in suffixes)


def detect_apply_method(apply_url: str | None, emails: list[str]) -> str | None:
    """"ats" (company applicant system), "email", or "form" (any other external page)."""
    url = (apply_url or "").strip()
    if url.lower().startswith("mailto:"):
        return "email"
    if url:
        host = (urlparse(url).hostname or "").lower()
        return "ats" if _host_matches(host, load_ats_hosts()) else "form"
    return "email" if emails else None
