"""The profile and preferences the dashboard edits."""

from __future__ import annotations

from typing import Any

from ..config import mutate_config, read_config_document


def get_config() -> dict[str, Any]:
    document, exists = read_config_document()
    return {"exists": exists, "config": document}


def update_config(profile: dict[str, Any], preferences: dict[str, Any]) -> dict[str, Any]:
    """Merge so keys the dashboard doesn't own (sources, companies, unknown extras) survive."""

    def mutate(document: dict[str, Any]) -> None:
        document["profile"] = {**document.get("profile", {}), **profile}
        document["preferences"] = {**document.get("preferences", {}), **preferences}

    return {"exists": True, "config": mutate_config(mutate)}


def block_company(company_key: str) -> None:
    """Record an ignored company's normalized key so future fetches mark it restricted."""

    def mutate(document: dict[str, Any]) -> None:
        blocked = [str(key) for key in document["companies"].get("blocked", []) or []]
        if company_key not in blocked:
            document["companies"]["blocked"] = [*blocked, company_key]

    mutate_config(mutate)
