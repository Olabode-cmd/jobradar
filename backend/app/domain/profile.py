"""Whether the search profile is filled in enough to crawl for it."""

from __future__ import annotations

from typing import Any

from ..core.errors import ConflictError

PROFILE_REQUIRED_MESSAGE = (
    "Fill in your profile first: set the job title you're looking for on the Profile page "
    "(or in jobradar.config.json). Nothing is fetched until then."
)


class ProfileIncompleteError(ConflictError):
    """A fetch was asked for before the user said what they are looking for."""


def is_profile_ready(profile: dict[str, Any] | None) -> bool:
    role = (profile or {}).get("role")
    return isinstance(role, str) and bool(role.strip())


def require_profile(profile: dict[str, Any] | None) -> None:
    """The single gate every crawl passes through."""
    if not is_profile_ready(profile):
        raise ProfileIncompleteError(PROFILE_REQUIRED_MESSAGE)


def target_countries(profile: dict[str, Any] | None, catalog: dict[str, Any]) -> list[str]:
    """The profile's country codes that the catalog knows, upper-cased, deduplicated, in order."""
    codes: list[str] = []
    for value in (profile or {}).get("targetCountries") or []:
        code = str(value).strip().upper()
        if code in catalog and code not in codes:
            codes.append(code)
    return codes
