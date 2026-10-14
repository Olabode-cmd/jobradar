"""The normalized job record: mapping a raw driver record onto the storage schema."""

from __future__ import annotations

import json
from typing import Any

from .contact import detect_apply_method, extract_emails
from .dates import to_iso
from .keys import company_key, dedupe_hash
from .text import fix_mojibake, html_to_text
from .urls import canonicalize_url


def is_usable(raw: dict[str, Any]) -> bool:
    """A record needs a title and a link; anything else is feed noise (legal notices, blanks)."""
    title = raw.get("title") or raw.get("position")
    link = raw.get("url") or raw.get("apply_url")
    return bool(str(title or "").strip() and str(link or "").strip())


def infer_remote(raw: dict[str, Any]) -> bool | None:
    """Remote flag: driver says so, or the text suggests it."""
    if raw.get("remote") is not None:
        return bool(raw.get("remote"))
    # Descriptions are deliberately excluded: nearly every posting mentions "remote" somewhere.
    text = " ".join(str(raw.get(k) or "") for k in ("location", "title", "tags")).lower()
    return True if "remote" in text else None


def _email_list(raw: dict[str, Any]) -> list[str]:
    given = raw.get("emails")
    if given:
        return [given] if isinstance(given, str) else [str(email) for email in given]
    return extract_emails(raw.get("description"))


def normalize_job(raw: dict[str, Any], source: dict[str, Any], now: str) -> dict[str, Any]:
    """Map a raw record to the normalized job schema used by the pipeline."""
    company = fix_mojibake(str(raw.get("company") or "Unknown"))
    title = fix_mojibake(str(raw.get("title") or raw.get("position") or "Untitled"))
    url = raw.get("url") or raw.get("apply_url") or ""
    first_seen = raw.get("first_seen_at") or now
    posted = (
        to_iso(raw.get("posted_at") or raw.get("date") or raw.get("publication_date") or raw.get("epoch"))
        or first_seen
    )
    location = raw.get("location") or raw.get("location_text") or ""
    apply_url = raw.get("apply_url") or url
    emails = _email_list(raw)

    return {
        "canonical_url": canonicalize_url(url),
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
        "apply_url": apply_url,
        "apply_method": raw.get("apply_method") or detect_apply_method(apply_url, emails),
        "emails": json.dumps(emails) if emails else None,
        "salary_text": raw.get("salary_text") or raw.get("salary"),
        "description": html_to_text(raw.get("description")),
        "low_confidence": bool(raw.get("low_confidence", False)),
    }
