"""Normalized keys used for dedupe and blocklists."""

from __future__ import annotations

import hashlib
import re

_LEGAL_SUFFIXES = (
    " incorporated", " inc", " llc", " ltd", " limited", " gmbh", " corp",
    " corporation", " co", " plc", " bv", " sarl", " s.a.",
)
_EMOJI_RE = re.compile("[\U00002190-\U00002BFF\U0000FE0F\U0001F000-\U0001FAFF]")


def company_key(name: str | None) -> str:
    """Normalize a company name for dedupe and blocklists.

    "Stripe, Inc." -> "stripe", "Acme Corp" -> "acme".
    """
    if not name:
        return ""
    s = re.sub(r"[^a-z0-9\s]", " ", name.lower())
    s = re.sub(r"\s+", " ", s).strip()
    for suffix in _LEGAL_SUFFIXES:
        if s.endswith(suffix):
            s = s[: -len(suffix)].rstrip()
            break
    return s


def normalize_title(title: str | None) -> str:
    """Lowercase title, strip parenthetical qualifiers and emoji."""
    if not title:
        return ""
    t = title.lower()
    t = re.sub(r"\([^)]*(remote|hybrid|onsite|m/f/d|f/m/d|full.?time|part.?time|contract)[^)]*\)", "", t)
    t = re.sub(r"\[[^\]]*\]", "", t)
    t = _EMOJI_RE.sub("", t)
    return re.sub(r"\s+", " ", t).strip()


def dedupe_hash(company: str | None, title: str | None) -> str | None:
    """Hash of company_key + normalized title. Location is deliberately excluded:
    boards describe the same job's location differently, so including it would
    guarantee missed merges.
    """
    key = f"{company_key(company)}|{normalize_title(title)}"
    if not key.strip("|"):
        return None
    return hashlib.sha1(key.encode("utf-8")).hexdigest()
