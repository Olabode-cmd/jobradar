"""Helpers shared by drivers that load several pages for one source."""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable
from typing import Any, TypeVar

log = logging.getLogger(__name__)

T = TypeVar("T")


def collect_pages(targets: Iterable[T], fetch_one: Callable[[T], list[dict[str, Any]]]) -> list[dict[str, Any]]:
    """Run `fetch_one` per target. One bad page is logged and skipped; every page failing raises.

    With a single target the original exception propagates, so a one-page source reports
    exactly what it reported before.
    """
    records: list[dict[str, Any]] = []
    failures: list[Exception] = []
    attempted = 0
    for target in targets:
        attempted += 1
        try:
            records.extend(fetch_one(target))
        except Exception as exc:
            log.warning("page failed (%s): %s", target, exc)
            failures.append(exc)
    if failures and not records:
        if attempted == 1:
            raise failures[0]
        raise RuntimeError(f"{failures[0]} (all {attempted} pages failed)") from failures[0]
    return records
