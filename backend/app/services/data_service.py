"""Resetting stored data. Your search settings live in the config file and are never touched."""

from __future__ import annotations

import sqlite3

from ..core.errors import ConflictError
from ..db.repositories import maintenance, run_lock


def clear_data(conn: sqlite3.Connection, keep_triaged: bool = False) -> dict[str, int]:
    """Delete stored jobs and run history. Refuses while a fetch is running.

    Takes the run lock for the duration so a fetch can't start halfway through the delete.
    """
    acquired, _ = run_lock.acquire(conn, force=False)
    if not acquired:
        raise ConflictError("A fetch is running. Wait for it to finish, then clear your jobs.")
    try:
        deleted, kept = maintenance.count_jobs(conn, keep_triaged)
        maintenance.clear_jobs_and_runs(conn, keep_triaged)
    finally:
        run_lock.release(conn)
    maintenance.compact(conn)
    return {"deleted": deleted, "kept": kept}
