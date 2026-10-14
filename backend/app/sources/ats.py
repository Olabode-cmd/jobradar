"""ATS drivers: one source per provider, iterating the companies tracked in the config.

Every provider exposes a public, keyless board feed. Each `Provider` knows its feed URL
and how to turn that feed into raw records; the shared fetch loop handles the rest.
"""

from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Callable
from urllib.parse import urlparse

from .http import http_get

COMPANY_FETCH_WORKERS = 4
MAX_RECORDS_PER_BOARD = 1000


@dataclass(frozen=True)
class Provider:
    id: str
    name: str
    feed_url: Callable[[str], str]
    parse: Callable[[Any, dict[str, Any]], list[dict[str, Any]]]
    fmt: str  # "json" or "xml"


def _join(*parts: Any) -> str:
    return ", ".join(str(part) for part in parts if part)


def _record(company: dict[str, Any], **fields: Any) -> dict[str, Any]:
    return {"company": company["name"], "company_id": company["slug"], **fields}


def _remote_if(flag: Any) -> bool | None:
    return True if flag else None


def _parse_greenhouse(payload: Any, company: dict[str, Any]) -> list[dict[str, Any]]:
    records = []
    for job in payload.get("jobs", []):
        location = job.get("location") or {}
        records.append(
            _record(
                {**company, "name": job.get("company_name") or company["name"]},
                title=job.get("title"),
                url=job.get("absolute_url"),
                location=location.get("name") if isinstance(location, dict) else None,
                description=html.unescape(job.get("content") or ""),
                date=job.get("first_published") or job.get("updated_at"),
            )
        )
    return records


def _parse_lever(payload: Any, company: dict[str, Any]) -> list[dict[str, Any]]:
    records = []
    for job in payload:
        categories = job.get("categories") or {}
        records.append(
            _record(
                company,
                title=job.get("text"),
                url=job.get("hostedUrl"),
                apply_url=job.get("applyUrl"),
                location=categories.get("location"),
                description=job.get("descriptionPlain"),
                date=job.get("createdAt"),
                remote=_remote_if(job.get("workplaceType") == "remote"),
            )
        )
    return records


def _parse_ashby(payload: Any, company: dict[str, Any]) -> list[dict[str, Any]]:
    records = []
    for job in payload.get("jobs", []):
        if job.get("isListed") is False:
            continue
        compensation = job.get("compensation") or {}
        records.append(
            _record(
                company,
                title=job.get("title"),
                url=job.get("jobUrl"),
                apply_url=job.get("applyUrl"),
                location=job.get("location"),
                description=job.get("descriptionHtml"),
                date=job.get("publishedAt"),
                remote=_remote_if(job.get("isRemote")),
                salary=compensation.get("compensationTierSummary"),
            )
        )
    return records


def _parse_workable(payload: Any, company: dict[str, Any]) -> list[dict[str, Any]]:
    name = payload.get("name") or company["name"]
    return [
        {
            **_record({**company, "name": name}),
            "title": job.get("title"),
            "url": job.get("url"),
            "apply_url": job.get("application_url"),
            "location": _join(job.get("city"), job.get("state"), job.get("country")),
            "description": job.get("description"),
            "date": job.get("published_on") or job.get("created_at"),
            "remote": _remote_if(job.get("telecommuting")),
        }
        for job in payload.get("jobs", [])
    ]


def _utc_suffix_to_offset(value: str | None) -> str | None:
    return value.replace(" UTC", "+00:00") if value else value


def _parse_recruitee(payload: Any, company: dict[str, Any]) -> list[dict[str, Any]]:
    records = []
    for offer in payload.get("offers", []):
        if offer.get("status") not in (None, "published"):
            continue
        records.append(
            _record(
                {**company, "name": offer.get("company_name") or company["name"]},
                title=offer.get("title"),
                url=offer.get("careers_url"),
                apply_url=offer.get("careers_apply_url"),
                location=offer.get("location"),
                description=_join_html(offer.get("description"), offer.get("requirements")),
                date=_utc_suffix_to_offset(offer.get("published_at") or offer.get("created_at")),
                remote=_remote_if(offer.get("remote")),
            )
        )
    return records


def _join_html(*parts: str | None) -> str:
    return "".join(part for part in parts if part)


def _parse_smartrecruiters(payload: Any, company: dict[str, Any]) -> list[dict[str, Any]]:
    records = []
    for posting in payload.get("content", []):
        location = posting.get("location") or {}
        identifier = (posting.get("company") or {}).get("identifier") or company["slug"]
        records.append(
            _record(
                company,
                title=posting.get("name"),
                url=f"https://jobs.smartrecruiters.com/{identifier}/{posting.get('id')}",
                location=location.get("fullLocation") or _join(location.get("city"), location.get("country")),
                date=posting.get("releasedDate"),
                remote=_remote_if(location.get("remote")),
            )
        )
    return records


def _parse_rss(payload: ET.Element, company: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        _record(
            company,
            title=(item.findtext("title") or "").strip(),
            url=(item.findtext("link") or "").strip(),
            description=item.findtext("description"),
            date=item.findtext("pubDate"),
        )
        for item in payload.iter("item")
    ]


def _parse_personio(payload: ET.Element, company: dict[str, Any]) -> list[dict[str, Any]]:
    records = []
    for position in payload.iter("position"):
        description = _join_html(
            *(
                f"<h3>{block.findtext('name') or ''}</h3>{block.findtext('value') or ''}"
                for block in position.iter("jobDescription")
            )
        )
        records.append(
            _record(
                {**company, "name": position.findtext("subcompany") or company["name"]},
                title=position.findtext("name"),
                url=f"https://{company['slug']}.jobs.personio.de/job/{position.findtext('id')}",
                location=position.findtext("office"),
                description=description,
                date=position.findtext("createdAt"),
            )
        )
    return records


def _parse_bamboohr(payload: Any, company: dict[str, Any]) -> list[dict[str, Any]]:
    records = []
    for job in payload.get("result", []):
        location = job.get("location") or {}
        ats_location = job.get("atsLocation") or {}
        records.append(
            _record(
                company,
                title=job.get("jobOpeningName"),
                url=f"https://{company['slug']}.bamboohr.com/careers/{job.get('id')}",
                location=_join(location.get("city"), location.get("state"), ats_location.get("country")),
                remote=_remote_if(job.get("isRemote")),
            )
        )
    return records


def _parse_breezy(payload: Any, company: dict[str, Any]) -> list[dict[str, Any]]:
    records = []
    for job in payload:
        location = job.get("location") or {}
        owner = job.get("company") or {}
        records.append(
            _record(
                {**company, "name": owner.get("name") or company["name"]},
                title=job.get("name"),
                url=job.get("url"),
                location=location.get("name"),
                date=job.get("published_date"),
                remote=_remote_if(location.get("is_remote")),
                salary=job.get("salary"),
            )
        )
    return records


PROVIDERS: dict[str, Provider] = {
    provider.id: provider
    for provider in (
        Provider("greenhouse", "Greenhouse", lambda s: f"https://boards-api.greenhouse.io/v1/boards/{s}/jobs?content=true", _parse_greenhouse, "json"),
        Provider("lever", "Lever", lambda s: f"https://api.lever.co/v0/postings/{s}?mode=json", _parse_lever, "json"),
        Provider("ashby", "Ashby", lambda s: f"https://api.ashbyhq.com/posting-api/job-board/{s}?includeCompensation=true", _parse_ashby, "json"),
        Provider("workable", "Workable", lambda s: f"https://apply.workable.com/api/v1/widget/accounts/{s}?details=true", _parse_workable, "json"),
        Provider("recruitee", "Recruitee", lambda s: f"https://{s}.recruitee.com/api/offers/", _parse_recruitee, "json"),
        Provider("smartrecruiters", "SmartRecruiters", lambda s: f"https://api.smartrecruiters.com/v1/companies/{s}/postings?limit=100", _parse_smartrecruiters, "json"),
        Provider("teamtailor", "Teamtailor", lambda s: f"https://{s}.teamtailor.com/jobs.rss", _parse_rss, "xml"),
        Provider("personio", "Personio", lambda s: f"https://{s}.jobs.personio.de/xml", _parse_personio, "xml"),
        Provider("bamboohr", "BambooHR", lambda s: f"https://{s}.bamboohr.com/careers/list", _parse_bamboohr, "json"),
        Provider("breezy", "Breezy", lambda s: f"https://{s}.breezy.hr/json", _parse_breezy, "json"),
    )
}

# Hostname -> (provider, how to read the slug). "path" = first path segment, "subdomain" = host prefix.
_HOST_RULES: list[tuple[re.Pattern[str], str, str]] = [
    (re.compile(r"^(?:job-)?boards(?:\.eu)?\.greenhouse\.io$"), "greenhouse", "path"),
    (re.compile(r"^jobs\.lever\.co$"), "lever", "path"),
    (re.compile(r"^jobs\.ashbyhq\.com$"), "ashby", "path"),
    (re.compile(r"^apply\.workable\.com$"), "workable", "path"),
    (re.compile(r"^(?:jobs|careers)\.smartrecruiters\.com$"), "smartrecruiters", "path"),
    (re.compile(r"^(?P<slug>[a-z0-9-]+)\.recruitee\.com$"), "recruitee", "subdomain"),
    (re.compile(r"^(?P<slug>[a-z0-9-]+)\.teamtailor\.com$"), "teamtailor", "subdomain"),
    (re.compile(r"^(?P<slug>[a-z0-9-]+)\.jobs\.personio\.(?:de|com)$"), "personio", "subdomain"),
    (re.compile(r"^(?P<slug>[a-z0-9-]+)\.bamboohr\.com$"), "bamboohr", "subdomain"),
    (re.compile(r"^(?P<slug>[a-z0-9-]+)\.breezy\.hr$"), "breezy", "subdomain"),
]
_SLUG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,80}$")


def detect_company(url: str) -> tuple[str, str] | None:
    """(provider, slug) from a careers-page URL, or None if the host isn't a known ATS."""
    text = url.strip()
    parsed = urlparse(text if "://" in text else f"https://{text}")
    host = (parsed.hostname or "").lower()
    for pattern, provider, slug_source in _HOST_RULES:
        match = pattern.match(host)
        if not match:
            continue
        if slug_source == "subdomain":
            slug = match.group("slug")
        else:
            segments = [segment for segment in parsed.path.split("/") if segment]
            slug = segments[0] if segments else ""
        if provider in ("greenhouse",) and slug == "embed":
            return None
        return (provider, slug) if _SLUG_RE.match(slug) else None
    return None


def _load_payload(provider: Provider, slug: str, timeout: int | None) -> Any:
    response = http_get(provider.feed_url(slug), timeout)
    if response.status == 404:
        raise RuntimeError("board not found (check the company's slug)")
    if response.status >= 400:
        raise RuntimeError(f"HTTP {response.status}")
    if provider.fmt == "json":
        return response.json()
    body = response.body
    return ET.fromstring(body.decode("utf-8", errors="replace") if isinstance(body, bytes) else body)


def _fetch_company(provider: Provider, company: dict[str, Any], timeout: int | None) -> dict[str, Any]:
    try:
        records = provider.parse(_load_payload(provider, company["slug"], timeout), company)[:MAX_RECORDS_PER_BOARD]
        return {"company": company, "records": records, "error": None}
    except Exception as exc:
        return {"company": company, "records": [], "error": f"{type(exc).__name__}: {exc}"}


def tracked_for_provider(config: Any, provider_id: str) -> list[dict[str, Any]]:
    entries = (config.companies or {}).get("tracked", []) or []
    valid = []
    for entry in entries:
        if not isinstance(entry, dict) or entry.get("provider") != provider_id or entry.get("enabled") is False:
            continue
        slug = str(entry.get("slug") or "")
        if _SLUG_RE.match(slug):
            valid.append({"name": str(entry.get("name") or slug), "slug": slug, "provider": provider_id})
    return valid


def fetch_ats(source: dict[str, Any], config: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Fetch every tracked company on this provider. Returns (records, per-company results)."""
    provider = PROVIDERS[source["provider"]]
    companies = tracked_for_provider(config, provider.id)
    if not companies:
        return [], []

    with ThreadPoolExecutor(max_workers=COMPANY_FETCH_WORKERS) as pool:
        results = list(pool.map(lambda company: _fetch_company(provider, company, source.get("timeout")), companies))

    records = [{**record, "source": source["id"]} for result in results for record in result["records"]]
    company_results = [
        {
            "key": f"{provider.id}:{result['company']['slug']}",
            "open_roles": len(result["records"]),
            "error": result["error"],
        }
        for result in results
    ]
    if all(result["error"] for result in results):
        raise RuntimeError(f"all {len(results)} boards failed; first error: {results[0]['error']}")
    return records, company_results


def ats_presets() -> list[dict[str, Any]]:
    return [
        {
            "id": provider.id,
            "name": provider.name,
            "tier": "A",
            "kind": "ats",
            "type": "ats",
            "provider": provider.id,
            "timeout": 30,
            "defaultEnabled": True,
        }
        for provider in PROVIDERS.values()
    ]
