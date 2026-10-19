"""`doctor`: hit every enabled source once and report pass/fail without storing."""

from __future__ import annotations

from typing import Any

from ..config import AppConfig
from ..sources import FetchContext, fetch_source
from .runner import select_sources


def run_doctor(config: AppConfig) -> list[dict[str, Any]]:
    ctx = FetchContext.from_config(config)
    rows: list[dict[str, Any]] = []
    for source in select_sources(config, None):
        result = fetch_source(source, ctx)
        rows.append(
            {
                "id": source["id"],
                "tier": source.get("tier", "B"),
                "kind": source.get("type", "selector"),
                "ok": result.error is None,
                "records": len(result.records),
                "error": result.error,
                "duration_ms": result.duration_ms,
            }
        )
    return rows
