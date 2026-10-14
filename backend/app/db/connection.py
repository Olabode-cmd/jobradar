"""SQLite lifecycle: auto-created app-data DB, WAL, busy_timeout, schema."""

from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path

from .schema import SCHEMA, SCHEMA_VERSION


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
    conn.execute("INSERT OR IGNORE INTO meta (key, value) VALUES ('schema_version', ?)", (SCHEMA_VERSION,))
    conn.commit()
    return conn
