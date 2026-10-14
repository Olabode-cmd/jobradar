"""Rule-based eligibility. Runs first, fast and free.

`evaluate` returns the verdict and, when the job is not plainly eligible, the reason, so
the dashboard can always say why.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from ..data import load_phrase_bank
from .dates import parse_datetime
from .salary import annual_salary_range


def _blocked_phrases(blocked_regions: Any) -> list[str]:
    if not blocked_regions:
        return []
    bank = load_phrase_bank()
    phrases = list(bank["generic"])
    for region in blocked_regions:
        phrases.extend(bank["regions"].get(str(region).upper(), []))
    return phrases


def _lowered(values: Any) -> list[str]:
    return [str(value).lower() for value in (values or []) if value]


def evaluate(job: dict[str, Any], profile: dict[str, Any]) -> tuple[str, str | None]:
    """Return (eligibility, reason): eligible | restricted | unclear."""
    title = str(job.get("title") or "").lower()
    text = " ".join(
        str(job.get(k) or "") for k in ("title", "description", "location_text", "salary_text")
    ).lower()

    if job.get("company_key") and job["company_key"] in (profile.get("blockedCompanies") or []):
        return "restricted", "company is on your ignore list"

    for phrase in _lowered(profile.get("rejectedPhrases")) + _blocked_phrases(profile.get("blockedRegions")):
        if phrase in text:
            return "restricted", f"mentions \"{phrase}\""

    for keyword in _lowered(profile.get("excludeKeywords")):
        if keyword in title:
            return "restricted", f"title contains \"{keyword}\""

    if profile.get("remoteOnly") and not job.get("remote_status"):
        return "restricted", "not remote"

    max_age = profile.get("maxAgeDays")
    if max_age and job.get("posted_at"):
        posted = parse_datetime(str(job["posted_at"]))
        if posted is not None and datetime.now(UTC) - posted > timedelta(days=max_age):
            return "restricted", f"posted more than {max_age} days ago"

    min_salary = profile.get("minSalary")
    if min_salary:
        salary = annual_salary_range(job.get("salary_text"))
        if salary is not None and salary[1] < min_salary:
            return "restricted", "pays below your minimum salary"

    include = _lowered(profile.get("includeKeywords"))
    if include and not any(keyword in text for keyword in include):
        return "unclear", "mentions none of your keywords"

    return "eligible", None


def apply_rules(job: dict[str, Any], profile: dict[str, Any]) -> str:
    return evaluate(job, profile)[0]
