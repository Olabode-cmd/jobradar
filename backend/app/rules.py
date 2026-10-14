"""Rule-based eligibility and scoring. Runs first, fast and free."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from typing import Any


def parse_datetime(value: str) -> datetime | None:
    """Parse ISO-8601 or RFC 2822 dates; naive dates become UTC-aware."""
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        try:
            dt = parsedate_to_datetime(str(value))
        except (TypeError, ValueError):
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt

# Region phrase bank: blocked regions expand into these rejected phrases.
# Community-maintained — add phrases for your region via a PR.
PHRASE_BANK: dict[str, list[str]] = {
    "US": [
        "must be located in the united states",
        "authorized to work in the united states",
        "authorized to work in the us",
        "us citizens",
        "us only",
        "must reside in the us",
        "work authorization in the us",
        "us work authorization",
        "green card or citizenship",
    ],
    "UK": [
        "right to work in the uk",
        "must be based in the uk",
        "uk work visa sponsorship",
    ],
    "EU": [
        "must be based in the eu",
        "right to work in the eu",
    ],
    "CA": [
        "must be located in canada",
        "canadian citizens",
        "work authorization in canada",
    ],
    "AU": [
        "must be located in australia",
        "australian citizens",
        "work rights in australia",
    ],
    "SG": [
        "must be located in singapore",
        "singapore work pass",
    ],
}

GENERIC_PHRASES = [
    "must reside in",
    "security clearance",
    "must be a us resident",
]


def _blocked_phrases(blocked_regions: Any) -> list[str]:
    if not blocked_regions:
        return []
    phrases = list(GENERIC_PHRASES)
    for region in blocked_regions:
        phrases.extend(PHRASE_BANK.get(str(region).upper(), []))
    return phrases


def apply_rules(job: dict[str, Any], profile: dict[str, Any]) -> str:
    """Return eligibility: eligible | restricted | unclear."""
    text = " ".join(
        str(job.get(k) or "") for k in ("title", "description", "location_text", "salary_text")
    ).lower()

    rejected = list(profile.get("rejectedPhrases", []) or []) + _blocked_phrases(profile.get("blockedRegions"))
    if rejected and any(phrase.lower() in text for phrase in rejected):
        return "restricted"

    if profile.get("remoteOnly") and not job.get("remote_status"):
        return "restricted"

    max_age = profile.get("maxAgeDays")
    if max_age and job.get("posted_at"):
        posted = parse_datetime(str(job["posted_at"]))
        if posted is not None and datetime.now(UTC) - posted > timedelta(days=max_age):
            return "restricted"

    include = [str(k).lower() for k in (profile.get("includeKeywords") or []) if k]
    if include and not any(k in text for k in include):
        return "unclear"

    return "eligible"


def score_job(job: dict[str, Any], profile: dict[str, Any]) -> tuple[float, list[str]]:
    """Weighted score with human-readable reasons (shown in the dashboard later)."""
    reasons: list[str] = []
    score = 0.0

    text = " ".join(str(job.get(k) or "") for k in ("title", "description")).lower()
    title = str(job.get("title") or "").lower()
    include = [str(k).lower() for k in (profile.get("includeKeywords") or []) if k]

    for kw in include:
        if kw in title:
            score += 3.0
            reasons.append(f"'{kw}' in title")
        elif kw in text:
            score += 1.5
            reasons.append(f"'{kw}' in description")

    if job.get("remote_status"):
        score += 1.0
        reasons.append("remote")

    if job.get("apply_url"):
        score += 0.5
        reasons.append("has apply link")

    posted = job.get("posted_at")
    if posted:
        posted_dt = parse_datetime(str(posted))
        if posted_dt is not None:
            days = (datetime.now(UTC) - posted_dt).days
            recency = max(0.0, 5.0 - days)
            if recency > 0:
                score += recency
                reasons.append(f"posted {days}d ago")

    if score == 0:
        score = 0.5

    return round(score, 2), reasons