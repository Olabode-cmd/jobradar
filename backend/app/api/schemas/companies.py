from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class CompanyAddIn(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    url: Annotated[str, Field(min_length=3, max_length=300)]


class CompanyImportIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    urls: Annotated[list[Annotated[str, Field(max_length=300)]], Field(min_length=1, max_length=500)]
