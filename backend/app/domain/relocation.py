"""Does a posting offer to pay for or help with the move?

"Willing to relocate" and "relocation required" are demands on the candidate, so only phrases
where the employer gives something count ("relocation support", "umzugskosten", "引越し支援").
A phrase is ignored when its clause negates it ("we cannot support relocation").
"""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Any

from ..data import load_relocation_phrases

_CLAUSE_BREAK = re.compile(r"[.!?;:,\n•—–]")
_BEFORE_CHARS = 50
_AFTER_CHARS = 30
_NEGATED_AFTER = re.compile(
    r"^\W{0,3}(?:is|are|will be|would be|can be|may be)?\s*(?:not|n't|never|unavailable)\b|^\W{0,3}nicht\b"
)


@lru_cache(maxsize=1)
def _offer_pattern() -> re.Pattern[str]:
    phrases = sorted(load_relocation_phrases()["offers"], key=len, reverse=True)
    # ASCII-only guard: Japanese text has no word boundaries, so any preceding character is fine.
    return re.compile("(?<![a-z0-9])(?:" + "|".join(re.escape(phrase) for phrase in phrases) + ")")


@lru_cache(maxsize=1)
def _negation_pattern() -> re.Pattern[str]:
    terms = sorted(load_relocation_phrases()["negations"], key=len, reverse=True)
    return re.compile("|".join(rf"(?<![a-z'])(?:{re.escape(term)})(?![a-z'])" for term in terms))


def _is_negated(text: str, start: int, end: int) -> bool:
    clause_start = max(0, start - _BEFORE_CHARS)
    breaks = list(_CLAUSE_BREAK.finditer(text, clause_start, start))
    if breaks:
        clause_start = breaks[-1].end()
    if _negation_pattern().search(text[clause_start:start]):
        return True
    return _NEGATED_AFTER.search(text[end : end + _AFTER_CHARS]) is not None


def offers_relocation(text: str | None) -> bool:
    """True when the text contains at least one relocation offer that is not negated."""
    if not text:
        return False
    lowered = text.lower().replace("\u2019", "'")
    return any(not _is_negated(lowered, m.start(), m.end()) for m in _offer_pattern().finditer(lowered))


def job_offers_relocation(job: dict[str, Any]) -> bool:
    """A source can vouch for every job it lists (`offers_relocation`); otherwise read the text."""
    if job.get("offers_relocation"):
        return True
    return offers_relocation(" ".join(str(job.get(key) or "") for key in ("title", "description", "location_text")))
