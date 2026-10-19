from __future__ import annotations

from pydantic import BaseModel, ConfigDict, StrictBool


class ClearDataIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    keep_triaged: StrictBool = False
