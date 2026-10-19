"""Rule-based eligibility. Runs first, fast and free.

`evaluate` returns the verdict and, when the job is not plainly eligible, the reason, so
run reports can say why a job was dropped. The pipeline only stores `eligible` jobs.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from typing import Any

from ..data import load_phrase_bank
from .dates import parse_datetime
from .salary import annual_salary_range

# With no keyword in the title, the description has to mention this many distinct keywords
# (or all of them, if the profile lists fewer).
MIN_BODY_KEYWORDS = 2


@lru_cache(maxsize=1024)
def _term_pattern(term: str) -> re.Pattern[str]:
    # Lookarounds rather than \b so terms such as ".net" or "c++" still match as whole words.
    # The optional "js" lets "react" and "node" match "ReactJS" and "NodeJS".
    return re.compile(rf"(?<!\w){re.escape(term)}(?:js)?(?!\w)")


def _contains(text: str, term: str) -> bool:
    """Whole-word match, so "lead" never matches "misleading" and "us only" never matches "focus only"."""
    return term in text and _term_pattern(term).search(text) is not None


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

    for phrase in _lowered(profile.get("rejectedPhrases")) + _lowered(_blocked_phrases(profile.get("blockedRegions"))):
        if _contains(text, phrase):
            return "restricted", f"mentions \"{phrase}\""

    for keyword in _lowered(profile.get("excludeKeywords")):
        if _contains(title, keyword):
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
    if include and not any(_contains(title, keyword) for keyword in include):
        needed = min(MIN_BODY_KEYWORDS, len(include))
        if sum(1 for keyword in include if _contains(text, keyword)) < needed:
            return "unclear", f"title has none of your keywords and the description has fewer than {needed}"

    return "eligible", None


def apply_rules(job: dict[str, Any], profile: dict[str, Any]) -> str:
    return evaluate(job, profile)[0]
