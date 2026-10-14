"""The registry of supported ATS providers."""

from __future__ import annotations

from typing import Any

from . import parsers
from .models import Provider

PROVIDERS: dict[str, Provider] = {
    provider.id: provider
    for provider in (
        Provider("greenhouse", "Greenhouse", lambda s: f"https://boards-api.greenhouse.io/v1/boards/{s}/jobs?content=true", parsers.parse_greenhouse, "json"),
        Provider("lever", "Lever", lambda s: f"https://api.lever.co/v0/postings/{s}?mode=json", parsers.parse_lever, "json"),
        Provider("ashby", "Ashby", lambda s: f"https://api.ashbyhq.com/posting-api/job-board/{s}?includeCompensation=true", parsers.parse_ashby, "json"),
        Provider("workable", "Workable", lambda s: f"https://apply.workable.com/api/v1/widget/accounts/{s}?details=true", parsers.parse_workable, "json"),
        Provider("recruitee", "Recruitee", lambda s: f"https://{s}.recruitee.com/api/offers/", parsers.parse_recruitee, "json"),
        Provider("smartrecruiters", "SmartRecruiters", lambda s: f"https://api.smartrecruiters.com/v1/companies/{s}/postings?limit=100", parsers.parse_smartrecruiters, "json"),
        Provider("teamtailor", "Teamtailor", lambda s: f"https://{s}.teamtailor.com/jobs.rss", parsers.parse_teamtailor, "xml"),
        Provider("personio", "Personio", lambda s: f"https://{s}.jobs.personio.de/xml", parsers.parse_personio, "xml"),
        Provider("bamboohr", "BambooHR", lambda s: f"https://{s}.bamboohr.com/careers/list", parsers.parse_bamboohr, "json"),
        Provider("breezy", "Breezy", lambda s: f"https://{s}.breezy.hr/json", parsers.parse_breezy, "json"),
    )
}


def ats_presets() -> list[dict[str, Any]]:
    """One source per provider; each iterates the companies tracked on that provider."""
    return [
        {
            "id": provider.id,
            "name": provider.name,
            "tier": "A",
            "kind": "ats",
            "type": "ats",
            "provider": provider.id,
            "timeout": 30,
            "defaultEnabled": True,
        }
        for provider in PROVIDERS.values()
    ]
