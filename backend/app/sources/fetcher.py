"""Dispatch a source to its driver. The one entry point the pipeline uses to fetch."""

from __future__ import annotations

import time
from typing import Any

from .drivers import ats, hackernews, json_board, rss, selector
from .models import FetchContext, SourceResult


def fetch_source(source: dict[str, Any], ctx: FetchContext) -> SourceResult:
    """Fetch one source and return raw records (or the error). Never raises."""
    t0 = time.perf_counter()
    companies: list[dict[str, Any]] = []
    try:
        kind = source.get("type", "selector")
        if kind == "api":
            records = json_board.fetch(source, ctx)
        elif kind == "rss":
            records = rss.fetch(source, ctx)
        elif kind == "ats":
            records, companies = ats.fetch(source, ctx)
        elif kind == "hn":
            records = hackernews.fetch(source, ctx)
        else:
            records = selector.fetch(source, ctx)
        return SourceResult(source["id"], records, None, int((time.perf_counter() - t0) * 1000), companies)
    except Exception as exc:
        return SourceResult(
            source["id"], error=f"{type(exc).__name__}: {exc}", duration_ms=int((time.perf_counter() - t0) * 1000)
        )
