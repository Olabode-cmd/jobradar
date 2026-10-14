"""Shared test helpers."""

from __future__ import annotations

import os
import tempfile
import unittest
from datetime import UTC, datetime
from typing import Any

from app.db import open_db

NOW = "2026-10-14T00:00:00+00:00"
BOARD = {"id": "board", "tier": "A", "kind": "board", "type": "api"}


def raw_job(n: int = 1, title: str = "Senior React Engineer", company: str = "Stripe", **overrides: Any) -> dict[str, Any]:
    """A raw driver record, as a source would emit it."""
    record = {
        "title": title,
        "company": company,
        "url": f"https://jobs.example.com/{n}",
        "location": "Remote",
        "description": "<p>React and TypeScript</p>",
        "date": "2026-10-10T00:00:00+00:00",
        "remote": True,
    }
    record.update(overrides)
    return record


def normalized_job(**overrides: Any) -> dict[str, Any]:
    """A normalized job, as the rules and scoring see it."""
    job = {
        "title": "Senior React Engineer",
        "description": "Build products with React and TypeScript.",
        "location_text": "Remote",
        "remote_status": "remote",
        "posted_at": datetime.now(UTC).isoformat(),
        "apply_url": "https://jobs.example.com/1",
    }
    job.update(overrides)
    return job


class TempDbTestCase(unittest.TestCase):
    """A fresh SQLite file per test, exposed as `self.conn`."""

    def setUp(self) -> None:
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        os.environ["JOBRADAR_DB"] = tmp.name
        self.conn = open_db()
        self.addCleanup(os.environ.pop, "JOBRADAR_DB", None)
        self.addCleanup(os.unlink, tmp.name)
        self.addCleanup(self.conn.close)
