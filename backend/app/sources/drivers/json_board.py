"""JSON API boards (RemoteOK, Remotive, Himalayas, Jobicy, Working Nomads, Arbeitnow).

Field names vary per board, so each field tries the known spellings in turn.
"""

from __future__ import annotations

from typing import Any

from ..http import http_get
from ..models import FetchContext


def _first(item: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = item.get(key)
        if value not in (None, "", []):
            return value
    return None


def _salary_text(item: dict[str, Any]) -> str | None:
    text = _first(item, "salary", "salary_text")
    if text:
        return str(text)
    low = _first(item, "salaryMin", "minSalary")
    high = _first(item, "salaryMax", "maxSalary")
    if not low and not high:
        return None
    currency = _first(item, "salaryCurrency", "currency") or ""
    period = _first(item, "salaryPeriod") or ""
    amount = f"{low}–{high}" if low and high else str(low or high)
    return " ".join(part for part in (str(currency), amount, str(period)) if part)


def _remote_flag(source: dict[str, Any], item: dict[str, Any]) -> bool | None:
    if source.get("allRemote"):
        return True
    flag = item.get("remote")
    return flag if isinstance(flag, bool) else None


def _job_items(source: dict[str, Any], data: Any) -> list[Any]:
    if isinstance(data, dict):
        jobs = data.get("jobs") or data.get("data") or []
        jobs = list(jobs.values()) if isinstance(jobs, dict) else jobs
    else:
        jobs = data
    if not isinstance(jobs, list):
        raise RuntimeError(f"unexpected JSON shape from {source['id']}: {type(jobs).__name__}")
    return jobs


def fetch(source: dict[str, Any], ctx: FetchContext) -> list[dict[str, Any]]:
    response = http_get(source["startUrl"], source.get("timeout"), contact=ctx.contact)
    if response.status >= 400:
        raise RuntimeError(f"HTTP {response.status}")

    records = []
    for item in _job_items(source, response.json()):
        if not isinstance(item, dict):
            continue
        url = _first(item, "url", "apply_url", "link", "guid") or ""
        restrictions = item.get("locationRestrictions")
        records.append(
            {
                "source": source["id"],
                "title": _first(item, "position", "title", "name", "jobTitle"),
                "company": _first(item, "company", "company_name", "companyName"),
                "url": url,
                "apply_url": _first(item, "apply_url", "application_url", "applicationLink") or url,
                "location": _first(item, "location", "candidate_required_location", "jobGeo", "city"),
                "description": _first(item, "description", "content", "jobDescription"),
                "salary": _salary_text(item),
                "date": _first(item, "date", "publication_date", "created_at", "pubDate", "pub_date", "publishedAt", "epoch"),
                "tags": item.get("tags"),
                "remote": _remote_flag(source, item),
                "region_restrictions": restrictions if isinstance(restrictions, list) and restrictions else None,
            }
        )
    return records
