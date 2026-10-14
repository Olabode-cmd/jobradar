"""Turn each provider's public feed into raw records. One function per provider."""

from __future__ import annotations

import html
import xml.etree.ElementTree as ET
from typing import Any

Company = dict[str, Any]
Records = list[dict[str, Any]]


def _join(*parts: Any) -> str:
    return ", ".join(str(part) for part in parts if part)


def _join_html(*parts: str | None) -> str:
    return "".join(part for part in parts if part)


def _record(company: Company, **fields: Any) -> dict[str, Any]:
    return {"company": company["name"], "company_id": company["slug"], **fields}


def _remote_if(flag: Any) -> bool | None:
    return True if flag else None


def parse_greenhouse(payload: Any, company: Company) -> Records:
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


def parse_lever(payload: Any, company: Company) -> Records:
    return [
        _record(
            company,
            title=job.get("text"),
            url=job.get("hostedUrl"),
            apply_url=job.get("applyUrl"),
            location=(job.get("categories") or {}).get("location"),
            description=job.get("descriptionPlain"),
            date=job.get("createdAt"),
            remote=_remote_if(job.get("workplaceType") == "remote"),
        )
        for job in payload
    ]


def parse_ashby(payload: Any, company: Company) -> Records:
    return [
        _record(
            company,
            title=job.get("title"),
            url=job.get("jobUrl"),
            apply_url=job.get("applyUrl"),
            location=job.get("location"),
            description=job.get("descriptionHtml"),
            date=job.get("publishedAt"),
            remote=_remote_if(job.get("isRemote")),
            salary=(job.get("compensation") or {}).get("compensationTierSummary"),
        )
        for job in payload.get("jobs", [])
        if job.get("isListed") is not False
    ]


def parse_workable(payload: Any, company: Company) -> Records:
    named = {**company, "name": payload.get("name") or company["name"]}
    return [
        _record(
            named,
            title=job.get("title"),
            url=job.get("url"),
            apply_url=job.get("application_url"),
            location=_join(job.get("city"), job.get("state"), job.get("country")),
            description=job.get("description"),
            date=job.get("published_on") or job.get("created_at"),
            remote=_remote_if(job.get("telecommuting")),
        )
        for job in payload.get("jobs", [])
    ]


def _utc_suffix_to_offset(value: str | None) -> str | None:
    return value.replace(" UTC", "+00:00") if value else value


def parse_recruitee(payload: Any, company: Company) -> Records:
    return [
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
        for offer in payload.get("offers", [])
        if offer.get("status") in (None, "published")
    ]


def parse_smartrecruiters(payload: Any, company: Company) -> Records:
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


def parse_teamtailor(payload: ET.Element, company: Company) -> Records:
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


def parse_personio(payload: ET.Element, company: Company) -> Records:
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


def parse_bamboohr(payload: Any, company: Company) -> Records:
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


def parse_breezy(payload: Any, company: Company) -> Records:
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
