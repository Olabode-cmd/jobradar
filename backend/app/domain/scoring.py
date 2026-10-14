"""Weighted fit score with human-readable reasons."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

from .dates import parse_datetime

TITLE_MATCH = 3.0
BODY_MATCH = 1.5
REMOTE_BONUS = 1.0
APPLY_LINK_BONUS = 0.5
OWN_BOARD_BONUS = 0.5
SENIORITY_MATCH = 1.5
SENIORITY_MISMATCH = -1.5
MAX_RECENCY_BONUS = 5.0
FALLBACK_SCORE = 0.5

_SENIORITY_LEVELS = (
    (re.compile(r"\b(?:intern|internship|trainee)\b"), 0),
    (re.compile(r"\b(?:junior|jr|entry[- ]level|graduate)\b"), 1),
    (re.compile(r"\b(?:senior|sr)\b"), 3),
    (re.compile(r"\b(?:lead|staff|principal)\b"), 4),
    (re.compile(r"\b(?:director|head of|vp)\b"), 5),
)


def _seniority(text: str) -> int | None:
    return next((level for pattern, level in _SENIORITY_LEVELS if pattern.search(text)), None)


def score_job(job: dict[str, Any], profile: dict[str, Any]) -> tuple[float, list[str]]:
    reasons: list[str] = []
    score = 0.0

    title = str(job.get("title") or "").lower()
    text = f"{title} {str(job.get('description') or '').lower()}"

    for keyword in (str(k).lower() for k in (profile.get("includeKeywords") or []) if k):
        if keyword in title:
            score += TITLE_MATCH
            reasons.append(f"'{keyword}' in title")
        elif keyword in text:
            score += BODY_MATCH
            reasons.append(f"'{keyword}' in description")

    wanted, offered = _seniority(str(profile.get("role") or "").lower()), _seniority(title)
    if wanted is not None and offered is not None:
        if wanted == offered:
            score += SENIORITY_MATCH
            reasons.append("seniority matches your role")
        elif abs(wanted - offered) >= 2:
            score += SENIORITY_MISMATCH
            reasons.append("seniority differs from your role")

    if job.get("remote_status"):
        score += REMOTE_BONUS
        reasons.append("remote")

    if job.get("apply_url"):
        score += APPLY_LINK_BONUS
        reasons.append("has apply link")
        if job.get("apply_method") == "ats":
            score += OWN_BOARD_BONUS
            reasons.append("applies on the company's own board")

    posted_dt = parse_datetime(str(job.get("posted_at") or ""))
    if posted_dt is not None:
        days = (datetime.now(UTC) - posted_dt).days
        recency = max(0.0, MAX_RECENCY_BONUS - days)
        if recency > 0:
            score += recency
            reasons.append(f"posted {days}d ago")

    return round(score if score > 0 else FALLBACK_SCORE, 2), reasons
