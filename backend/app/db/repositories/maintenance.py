"""Bulk deletes for resetting the database."""

from __future__ import annotations

import sqlite3


def count_jobs(conn: sqlite3.Connection, keep_triaged: bool) -> tuple[int, int]:
    """(jobs a clear would delete, jobs it would keep)."""
    total = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    kept = conn.execute("SELECT COUNT(*) FROM jobs WHERE status != 'new'").fetchone()[0] if keep_triaged else 0
    return total - kept, kept


def clear_jobs_and_runs(conn: sqlite3.Connection, keep_triaged: bool) -> None:
    """Delete jobs (all, or only untriaged ones) and all run history.

    Source and company health is kept: it describes the boards, not your jobs. Triaged jobs
    are the ones whose status is not 'new'; they stay so ignored and rejected jobs don't come
    back as new on the next fetch. Job ids are never reused (AUTOINCREMENT), so a dashboard
    tab left open can't act on a different job after a clear.
    """
    if keep_triaged:
        conn.execute("DELETE FROM jobs WHERE status = 'new'")
        conn.execute("DELETE FROM job_sources WHERE job_id NOT IN (SELECT id FROM jobs)")
    else:
        conn.execute("DELETE FROM jobs")
        conn.execute("DELETE FROM job_sources")
    conn.execute("DELETE FROM run_sources")
    conn.execute("DELETE FROM runs")
    conn.commit()


def compact(conn: sqlite3.Connection) -> None:
    """Give freed pages back to the file. Best effort: another open connection can block it."""
    try:
        conn.execute("VACUUM")
    except sqlite3.OperationalError:
        pass  # the data is already gone; only the file size is unchanged
