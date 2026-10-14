"""Normalization: canonical URLs, company/title keys, and the normalized job schema."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from html.parser import HTMLParser
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from .rules import parse_datetime

MAX_DESCRIPTION_CHARS = 20_000
BLOCK_TAGS = {"p", "br", "div", "li", "ul", "ol", "tr", "h1", "h2", "h3", "h4", "h5", "h6"}
SKIPPED_TAGS = {"script", "style"}

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


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in SKIPPED_TAGS:
            self._skip_depth += 1
        elif tag in BLOCK_TAGS:
            self.parts.append("\n- " if tag == "li" else "\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in SKIPPED_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
        elif tag in BLOCK_TAGS and tag != "li":
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._skip_depth:
            self.parts.append(data)


_MOJIBAKE = re.compile("[\u00c2\u00c3\u00e2][\u0080-\u00bf]")


def fix_mojibake(text: str) -> str:
    """Undo UTF-8 text that an upstream feed double-encoded as Latin-1 ("\u00e2\u0080\u0094" for an em dash)."""
    if not _MOJIBAKE.search(text):
        return text
    try:
        return text.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text


def html_to_text(value: Any) -> str | None:
    """Plain text from an HTML or text description: tags dropped, blocks become lines."""
    if not value:
        return None
    text = fix_mojibake(str(value))
    if "<" in text:
        extractor = _TextExtractor()
        extractor.feed(text)
        extractor.close()
        text = "".join(extractor.parts)
    lines = [" ".join(line.split()) for line in text.splitlines()]
    collapsed = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()
    return collapsed[:MAX_DESCRIPTION_CHARS] or None


def to_iso(value: Any) -> str | None:
    """ISO-8601 UTC string from ISO/RFC 2822 text or an epoch (seconds or milliseconds)."""
    if value is None or value == "" or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        seconds = value / 1000 if value > 1e11 else value
        try:
            return datetime.fromtimestamp(seconds, UTC).isoformat()
        except (OverflowError, OSError, ValueError):
            return None
    parsed = parse_datetime(str(value))
    return parsed.isoformat() if parsed else None


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


def is_usable(raw: dict[str, Any]) -> bool:
    """A record needs a title and a link; anything else is feed noise (legal notices, blanks)."""
    title = raw.get("title") or raw.get("position")
    link = raw.get("url") or raw.get("apply_url")
    return bool(str(title or "").strip() and str(link or "").strip())


def normalize_job(raw: dict[str, Any], source: dict[str, Any], now: str) -> dict[str, Any]:
    """Map a raw record to the normalized job schema used by the pipeline."""
    company = fix_mojibake(str(raw.get("company") or "Unknown"))
    title = fix_mojibake(str(raw.get("title") or raw.get("position") or "Untitled"))
    url = raw.get("url") or raw.get("apply_url") or ""
    canonical = canonicalize_url(url)
    first_seen = raw.get("first_seen_at") or now
    posted = (
        to_iso(raw.get("posted_at") or raw.get("date") or raw.get("publication_date") or raw.get("epoch"))
        or first_seen
    )
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
        "emails": normalize_email_list(raw.get("emails")),
        "salary_text": raw.get("salary_text") or raw.get("salary"),
        "description": html_to_text(raw.get("description")),
        "low_confidence": bool(raw.get("low_confidence", False)),
    }


def normalize_email_list(emails: Any) -> str | None:
    """Serialize an email list (or single address) to JSON text for storage."""
    if not emails:
        return None
    if isinstance(emails, str):
        return emails
    return json.dumps(list(emails))