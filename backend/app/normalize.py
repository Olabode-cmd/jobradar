"""Normalization: canonical URLs, company/title keys, and the normalized job schema."""

from __future__ import annotations

import hashlib
import re
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

LEGAL_SUFFIXES = (
    " incorporated",
    " inc",
    " llc",
    " ltd",
    " limited",
    " gmbh",
    " corp",
    " corporation",
    " co",
    " plc",
    " bv",
    " sarl",
    " s.a.",
)

TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "mc_cid", "mc_eid", "ref", "source", "spm", "yclid",
}

_EMOJI_RE = re.compile("[\U00002190-\U00002BFF\U0000FE0F\U0001F000-\U0001FAFF]")


def company_key(name: str | None) -> str:
    """Normalize a company name for dedupe and blocklists.

    "Stripe, Inc." -> "stripe", "Acme Corp" -> "acme".
    """
    if not name:
        return ""
    s = re.sub(r"[^a-z0-9\s]", " ", name.lower())
    s = re.sub(r"\s+", " ", s).strip()
    for suffix in LEGAL_SUFFIXES:
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


def canonicalize_url(url: str | None) -> str:
    """Strip tracking parameters and fragments from a URL."""
    if not url:
        return ""
    parsed = urlparse(url.strip())
    kept = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True) if k.lower() not in TRACKING_PARAMS]
    clean_query = urlencode(kept)
    return urlunparse((parsed.scheme, parsed.netloc.lower(), parsed.path, parsed.params, clean_query, ""))


def infer_remote(raw: dict[str, Any]) -> bool | None:
    """Remote flag: driver says so, or the text suggests it."""
    if raw.get("remote") is not None:
        return bool(raw.get("remote"))
    text = " ".join(
        str(raw.get(k) or "") for k in ("location", "title", "tags", "description")
    ).lower()
    if "remote" in text:
        return True
    return None


def normalize_job(raw: dict[str, Any], source: dict[str, Any], now: str) -> dict[str, Any]:
    """Map a raw record to the normalized job schema used by the pipeline."""
    company = raw.get("company") or "Unknown"
    title = raw.get("title") or raw.get("position") or "Untitled"
    url = raw.get("url") or raw.get("apply_url") or ""
    canonical = canonicalize_url(url)
    first_seen = raw.get("first_seen_at") or now
    posted = raw.get("posted_at") or raw.get("date") or raw.get("publication_date") or first_seen
    tags = raw.get("tags") or []
    if isinstance(tags, str):
        tags = [tags]
    location = raw.get("location") or raw.get("location_text") or ""

    return {
        "canonical_url": canonical,
        "dedupe_hash": dedupe_hash(company, title),
        "company_key": company_key(company),
        "company_id": raw.get("company_id"),
        "company": company,
        "title": title,
        "location_text": str(location),
        "remote_status": "remote" if infer_remote(raw) else None,
        "region_restrictions": raw.get("region_restrictions"),
        "posted_at": posted,
        "first_seen_at": first_seen,
        "apply_url": raw.get("apply_url") or url,
        "apply_method": raw.get("apply_method"),
        "emails": raw.get("emails"),
        "salary_text": raw.get("salary_text") or raw.get("salary"),
        "description": raw.get("description"),
        "low_confidence": bool(raw.get("low_confidence", False)),
    }


def normalize_email_list(emails: Any) -> str | None:
    """Serialize an email list (or single address) to JSON text for storage."""
    if not emails:
        return None
    if isinstance(emails, str):
        return emails
    import json

    return json.dumps(list(emails))