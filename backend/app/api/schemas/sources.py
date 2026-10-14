from __future__ import annotations

from pydantic import BaseModel, ConfigDict, StrictBool


class ToggleIn(BaseModel):
    """Enable or disable a source or a tracked company."""

    model_config = ConfigDict(extra="forbid")

    enabled: StrictBool
