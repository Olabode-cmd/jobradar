"""Request models for the config API. Field names match jobradar.config.json keys."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictFloat,
    StrictInt,
    field_validator,
)

MAX_LIST_ITEMS = 200
MAX_ITEM_LENGTH = 120


def _clean_list(values: list[str]) -> list[str]:
    """Trim, drop blanks and case-insensitive duplicates, keep first-seen order."""
    seen: set[str] = set()
    cleaned: list[str] = []
    for value in values:
        text = value.strip()
        if not text or text.lower() in seen:
            continue
        if len(text) > MAX_ITEM_LENGTH:
            raise ValueError(f"entries must be at most {MAX_ITEM_LENGTH} characters")
        seen.add(text.lower())
        cleaned.append(text)
    return cleaned


TermList = Annotated[list[str], Field(max_length=MAX_LIST_ITEMS)]


class ProfileIn(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    role: Annotated[str, Field(min_length=1, max_length=MAX_ITEM_LENGTH)]
    includeKeywords: TermList
    excludeKeywords: TermList
    rejectedPhrases: TermList
    remoteOnly: StrictBool
    blockedRegions: TermList
    timezonesOverlap: Annotated[str, Field(max_length=MAX_ITEM_LENGTH)] | None
    minSalary: Annotated[StrictInt | StrictFloat, Field(ge=0)] | None
    maxAgeDays: Annotated[StrictInt, Field(ge=1, le=3650)] | None

    @field_validator(
        "includeKeywords", "excludeKeywords", "rejectedPhrases", "blockedRegions", mode="after"
    )
    @classmethod
    def _tidy_lists(cls, values: list[str]) -> list[str]:
        return _clean_list(values)

    @field_validator("timezonesOverlap", mode="after")
    @classmethod
    def _blank_to_none(cls, value: str | None) -> str | None:
        return value or None


class PreferencesIn(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    userAgentContact: Annotated[str, Field(max_length=200)]


JobStatus = Literal["new", "saved", "applied", "interviewing", "rejected", "ignored"]


class JobUpdateIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: JobStatus | None = None
    notes: Annotated[str, Field(max_length=5000)] | None = None


class BulkStatusIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ids: Annotated[list[StrictInt], Field(min_length=1, max_length=500)]
    status: JobStatus


class RunStartIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sources: Annotated[list[Annotated[str, Field(max_length=120)]], Field(max_length=100)] | None = None
    dry_run: StrictBool = False


class ConfigUpdateIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    profile: ProfileIn
    preferences: PreferencesIn
