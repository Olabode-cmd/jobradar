"""In-memory progress of the current (or most recent) run, read by the dashboard."""

from __future__ import annotations

import threading
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any


class RunProgress:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._state: dict[str, Any] | None = None

    def start(self, run_id: int, started_at: str, source_ids: list[str], dry_run: bool) -> None:
        with self._lock:
            self._state = {
                "run_id": run_id,
                "state": "running",
                "started_at": started_at,
                "finished_at": None,
                "dry_run": dry_run,
                "error": None,
                "stage": "fetch",
                "llm": None,
                "sources": [{"id": source_id, "state": "running"} for source_id in source_ids],
            }

    def update_source(self, source_id: str, **fields: Any) -> None:
        with self._lock:
            if self._state is None:
                return
            for source in self._state["sources"]:
                if source["id"] == source_id:
                    source.update(fields)

    def set_stage(self, stage: str) -> None:
        with self._lock:
            if self._state is not None:
                self._state["stage"] = stage

    def finish(self, error: str | None = None, llm: dict[str, Any] | None = None) -> None:
        with self._lock:
            if self._state is None:
                return
            self._state["state"] = "failed" if error else "finished"
            self._state["error"] = error
            self._state["llm"] = llm
            self._state["finished_at"] = datetime.now(UTC).isoformat()

    def snapshot(self) -> dict[str, Any] | None:
        with self._lock:
            return deepcopy(self._state)


PROGRESS = RunProgress()
