"""Work out which ATS provider and board slug a careers-page URL belongs to."""

from __future__ import annotations

import re
from urllib.parse import urlparse

SLUG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,80}$")

# host pattern -> (provider, where the slug lives). "path" = first path segment; "subdomain" = host prefix.
_HOST_RULES: list[tuple[re.Pattern[str], str, str]] = [
    (re.compile(r"^(?:job-)?boards(?:\.eu)?\.greenhouse\.io$"), "greenhouse", "path"),
    (re.compile(r"^jobs\.lever\.co$"), "lever", "path"),
    (re.compile(r"^jobs\.ashbyhq\.com$"), "ashby", "path"),
    (re.compile(r"^apply\.workable\.com$"), "workable", "path"),
    (re.compile(r"^(?:jobs|careers)\.smartrecruiters\.com$"), "smartrecruiters", "path"),
    (re.compile(r"^(?P<slug>[a-z0-9-]+)\.recruitee\.com$"), "recruitee", "subdomain"),
    (re.compile(r"^(?P<slug>[a-z0-9-]+)\.teamtailor\.com$"), "teamtailor", "subdomain"),
    (re.compile(r"^(?P<slug>[a-z0-9-]+)\.jobs\.personio\.(?:de|com)$"), "personio", "subdomain"),
    (re.compile(r"^(?P<slug>[a-z0-9-]+)\.bamboohr\.com$"), "bamboohr", "subdomain"),
    (re.compile(r"^(?P<slug>[a-z0-9-]+)\.breezy\.hr$"), "breezy", "subdomain"),
]


def detect_company(url: str) -> tuple[str, str] | None:
    """(provider, slug) from a careers-page URL, or None if the host isn't a known ATS."""
    text = url.strip()
    parsed = urlparse(text if "://" in text else f"https://{text}")
    host = (parsed.hostname or "").lower()
    for pattern, provider, slug_source in _HOST_RULES:
        match = pattern.match(host)
        if not match:
            continue
        if slug_source == "subdomain":
            slug = match.group("slug")
        else:
            segments = [segment for segment in parsed.path.split("/") if segment]
            slug = segments[0] if segments else ""
        if provider == "greenhouse" and slug == "embed":
            return None
        return (provider, slug) if SLUG_RE.match(slug) else None
    return None
