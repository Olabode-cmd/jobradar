from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StrictBool


class RunStartIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sources: Annotated[list[Annotated[str, Field(max_length=120)]], Field(max_length=100)] | None = None
    dry_run: StrictBool = False
