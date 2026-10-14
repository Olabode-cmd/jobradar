"""The optional LLM pass: assess the best unassessed jobs after a run, capped per run, results cached."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from ..db.repositories import llm as store
from ..llm import FATAL_KINDS, LlmClient, LlmError
from ..llm.assess import assess_job

MAX_JOBS_PER_RUN = 50
FIT_SCORE_WEIGHT = 0.5


def _load_reasons(text: str | None) -> list[str]:
    try:
        value = json.loads(text) if text else []
    except json.JSONDecodeError:
        return []
    return [str(item) for item in value] if isinstance(value, list) else []


def run_llm_pass(
    conn: sqlite3.Connection, client: LlmClient, profile: dict[str, Any], limit: int = MAX_JOBS_PER_RUN
) -> dict[str, Any]:
    """Returns {assessed, failed, message}. A fatal error (bad key, rate limit) stops the pass early."""
    stats: dict[str, Any] = {"assessed": 0, "failed": 0, "message": None}

    for row in store.pending_jobs(conn, limit):
        try:
            assessment = assess_job(client, profile, dict(row))
        except LlmError as exc:
            stats["failed"] += 1
            if exc.kind in FATAL_KINDS:
                stats["message"] = str(exc)
                break
            continue

        reasons = _load_reasons(row["score_reasons"])
        eligibility = row["eligibility"]
        if assessment.eligible == "no":
            eligibility = "restricted"
            reasons.insert(0, f"restricted (AI): {assessment.reason}")
        elif assessment.eligible == "yes" and eligibility == "unclear":
            eligibility = "eligible"
        reasons.append(f"AI fit {assessment.fit}/10: {assessment.reason}")

        score = round((row["score"] or 0) + assessment.fit * FIT_SCORE_WEIGHT, 2)
        store.save_assessment(conn, row["id"], assessment.as_dict(), eligibility, score, reasons)
        stats["assessed"] += 1

    return stats
