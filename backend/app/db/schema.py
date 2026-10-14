"""SQLite schema. The database is state only: no settings, no profiles."""

SCHEMA_VERSION = "1"

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
