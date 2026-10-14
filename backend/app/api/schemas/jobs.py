from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt

JobStatus = Literal["new", "saved", "applied", "interviewing", "rejected", "ignored"]


class JobUpdateIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: JobStatus | None = None
    notes: Annotated[str, Field(max_length=5000)] | None = None


class BulkStatusIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ids: Annotated[list[StrictInt], Field(min_length=1, max_length=500)]
    status: JobStatus
