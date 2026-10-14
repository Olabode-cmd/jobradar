"""Best-effort salary parsing for the minimum-salary rule."""

from __future__ import annotations

import re

_AMOUNT = re.compile(r"(?P<cur>[$€£])?\s*(?P<num>\d[\d,]*(?:\.\d+)?)\s*(?P<k>[kK])?\b")
_CURRENCY_HINT = re.compile(r"[$€£]|\b(?:USD|EUR|GBP|CAD|AUD|CHF|SEK|NOK|DKK|PLN)\b|\d\s*[kK]\b")
_PERIODS = (
    (re.compile(r"\b(?:hour|hr|hourly)\b|/\s*h\b", re.IGNORECASE), 2080),
    (re.compile(r"\b(?:day|daily)\b", re.IGNORECASE), 260),
    (re.compile(r"\b(?:week|weekly)\b", re.IGNORECASE), 52),
    (re.compile(r"\b(?:month|monthly|mo)\b", re.IGNORECASE), 12),
)
_MIN_PLAUSIBLE_ANNUAL = 1000


def annual_salary_range(text: str | None) -> tuple[float, float] | None:
    """(low, high) per year from text like "$80K - $120K" or "USD 50-70 hourly". None if unsure."""
    if not text or not _CURRENCY_HINT.search(text):
        return None

    amounts = []
    for match in _AMOUNT.finditer(text):
        value = float(match.group("num").replace(",", ""))
        if match.group("k"):
            value *= 1000
        amounts.append(value)
    if not amounts:
        return None

    multiplier = next((factor for pattern, factor in _PERIODS if pattern.search(text)), 1)
    low, high = min(amounts[:2]), max(amounts[:2])
    low, high = low * multiplier, high * multiplier
    if high < _MIN_PLAUSIBLE_ANNUAL:
        return None
    return low, high
