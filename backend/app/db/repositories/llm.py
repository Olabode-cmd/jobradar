"""Jobs awaiting an LLM assessment, and storing the result."""

from __future__ import annotations

import json
import sqlite3
from typing import Any


def pending_jobs(conn: sqlite3.Connection, limit: int) -> list[sqlite3.Row]:
    """New, not-restricted jobs with no cached result, best rule score first."""
    return conn.execute(
        """SELECT id, title, company, location_text, description, salary_text, score, score_reasons, eligibility
           FROM jobs
           WHERE llm_result IS NULL AND status = 'new' AND eligibility IN ('eligible', 'unclear')
           ORDER BY score DESC, id DESC LIMIT ?""",
        (limit,),
    ).fetchall()


def save_assessment(
    conn: sqlite3.Connection,
    job_id: int,
    assessment: dict[str, Any],
    eligibility: str,
    score: float,
    reasons: list[str],
) -> None:
    conn.execute(
        "UPDATE jobs SET llm_result = ?, eligibility = ?, score = ?, score_reasons = ? WHERE id = ?",
        (json.dumps(assessment), eligibility, score, json.dumps(reasons), job_id),
    )
    conn.commit()
