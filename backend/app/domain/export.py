"""Render jobs as CSV or Markdown for export."""

from __future__ import annotations

import csv
import io
from typing import Any

COLUMNS = (
    "id", "title", "company", "location", "remote", "status", "eligibility", "score",
    "posted_at", "apply_url", "apply_method", "emails", "salary", "notes", "applied_at", "sources",
)
_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def _safe_cell(value: Any) -> Any:
    """Stop spreadsheets from running a posting's text as a formula (CSV injection)."""
    if isinstance(value, str) and value.startswith(_FORMULA_PREFIXES):
        return f"'{value}"
    return value


def _row(job: dict[str, Any]) -> list[Any]:
    return [
        job["id"], job["title"], job["company"], job["location_text"],
        "yes" if job["remote"] else "no", job["status"], job["eligibility"], job["score"],
        job["posted_at"], job["apply_url"], job["apply_method"], "; ".join(job["emails"]),
        job["salary_text"], job["notes"], job["applied_at"], "; ".join(job["sources"]),
    ]


def jobs_to_csv(jobs: list[dict[str, Any]]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(COLUMNS)
    for job in jobs:
        writer.writerow([_safe_cell(cell) for cell in _row(job)])
    return buffer.getvalue()


def _escape_markdown(text: str) -> str:
    return text.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]").replace("\n", " ")


def jobs_to_markdown(jobs: list[dict[str, Any]]) -> str:
    """One section per status, one bullet per job."""
    by_status: dict[str, list[dict[str, Any]]] = {}
    for job in jobs:
        by_status.setdefault(job["status"], []).append(job)

    lines = ["# JobRadar export", ""]
    for status, items in by_status.items():
        lines += [f"## {status.capitalize()} ({len(items)})", ""]
        for job in items:
            title = _escape_markdown(str(job["title"] or "Untitled"))
            heading = f"[{title}]({job['apply_url']})" if job["apply_url"] else title
            details = [job["company"], job["location_text"], f"score {job['score']}" if job["score"] is not None else None]
            lines.append(f"- {heading} — {' · '.join(str(d) for d in details if d)}")
            if job["notes"]:
                lines.append(f"  - Notes: {_escape_markdown(str(job['notes']))}")
            if job["emails"]:
                lines.append(f"  - Contact: {', '.join(job['emails'])}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"

