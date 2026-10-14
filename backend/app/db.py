"""SQLite lifecycle: auto-created app-data DB, WAL, busy_timeout, schema.

The database is state only — no settings, no profiles. Drop it and nothing
about your search is lost; the config file is the source of truth for that.
"""

from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_url        TEXT NOT NULL UNIQUE,
    dedupe_hash          TEXT,
    company_key          TEXT NOT NULL,
    company_id           TEXT,
    company              TEXT,
    title                TEXT,
    location_text        TEXT,
    remote_status        TEXT,
    region_restrictions  TEXT,
    posted_at            TEXT,
    first_seen_at        TEXT,
    apply_url            TEXT,
    apply_method         TEXT,
    emails               TEXT,
    salary_text          TEXT,
    description          TEXT,
    score                REAL,
    score_reasons        TEXT,
    llm_result           TEXT,
    eligibility          TEXT,
    status               TEXT NOT NULL DEFAULT 'new',
    status_changed_at    TEXT,
    reposted             INTEGER NOT NULL DEFAULT 0,
    low_confidence       INTEGER NOT NULL DEFAULT 0,
    notes                TEXT,
    applied_at           TEXT
);
CREATE INDEX IF NOT EXISTS idx_jobs_status_eligibility ON jobs (status, eligibility);
CREATE INDEX IF NOT EXISTS idx_jobs_company_key ON jobs (company_key);
CREATE INDEX IF NOT EXISTS idx_jobs_dedupe_hash ON jobs (dedupe_hash);

CREATE TABLE IF NOT EXISTS job_sources (
    job_id     INTEGER NOT NULL,
    source_id  TEXT NOT NULL,
    url        TEXT NOT NULL,
    seen_at    TEXT,
    PRIMARY KEY (job_id, source_id, url)
);

CREATE TABLE IF NOT EXISTS source_state (
    source_id       TEXT PRIMARY KEY,
    last_run_at     TEXT,
    last_status     TEXT,
    last_error      TEXT,
    last_success_at TEXT
);

CREATE TABLE IF NOT EXISTS company_state (
    company_key      TEXT PRIMARY KEY,
    last_checked_at  TEXT,
    last_error       TEXT,
    open_roles       INTEGER
);

CREATE TABLE IF NOT EXISTS runs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at  TEXT,
    finished_at TEXT,
    trigger     TEXT,
    summary     TEXT
);

CREATE TABLE IF NOT EXISTS run_sources (
    run_id       INTEGER NOT NULL,
    source_id    TEXT NOT NULL,
    fetched      INTEGER,
    new          INTEGER,
    errors       INTEGER,
    duration_ms  INTEGER,
    PRIMARY KEY (run_id, source_id)
);

CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);
"""


def default_db_path() -> Path:
    """OS app-data location, never the cloned repo (re-clones keep history)."""
    override = os.environ.get("JOBRADAR_DB")
    if override:
        return Path(override)
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / "jobradar" / "jobradar.db"


def open_db() -> sqlite3.Connection:
    """Connect, apply pragmas, ensure the schema exists. Caller closes."""
    path = default_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    lowered = str(path).lower()
    if "onedrive" in lowered or "dropbox" in lowered:
        print(
            f"warning: database is inside a synced folder ({path}); SQLite WAL + sync "
            "can corrupt data — set JOBRADAR_DB to a local path",
            file=sys.stderr,
        )
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.executescript(SCHEMA)
    conn.execute("INSERT OR IGNORE INTO meta (key, value) VALUES ('schema_version', '1')")
    conn.commit()
    return conn