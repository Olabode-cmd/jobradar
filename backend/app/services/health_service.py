"""The /api/health report."""

from __future__ import annotations

from typing import Any

from ..config import load_config
from ..db import open_db
from ..llm import load_llm_settings


def health_report() -> dict[str, Any]:
    config = load_config()
    conn = open_db()
    try:
        conn.execute("SELECT 1 FROM meta LIMIT 1")
        db = "ok"
    except Exception as exc:  # surface any DB failure in the report
        db = f"error: {exc}"
    finally:
        conn.close()

    return {
        "status": "ok",
        "db": db,
        "config_loaded": config.present,
        "profile_role": config.profile_role,
        "config_errors": config.errors,
        "llm": load_llm_settings().enabled,
    }
