"""URL canonicalization for dedupe."""

from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "mc_cid", "mc_eid", "ref", "source", "spm", "yclid",
}


def canonicalize_url(url: str | None) -> str:
    """Strip tracking parameters and fragments from a URL."""
    if not url:
        return ""
    parsed = urlparse(url.strip())
    kept = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True) if k.lower() not in TRACKING_PARAMS]
    return urlunparse((parsed.scheme, parsed.netloc.lower(), parsed.path, parsed.params, urlencode(kept), ""))
