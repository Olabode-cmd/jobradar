from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


class SettingsUpdateIn(BaseModel):
    """Omitted fields are left unchanged; an empty string clears the value."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    api_key: Annotated[str, Field(max_length=300)] | None = None
    provider: Literal["", "anthropic", "openai-compatible"] | None = None
    model: Annotated[str, Field(max_length=100)] | None = None
    base_url: Annotated[str, Field(max_length=300)] | None = None
