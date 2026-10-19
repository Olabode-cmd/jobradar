"""Wellfound (Tier C): logged-out role-and-location listing pages.

Wellfound sits behind bot protection, so this needs the stealth browser, and expect it to
break. Listings are read from the Apollo cache Next.js embeds in `__NEXT_DATA__`; each job
carries its full description, which is what the relocation rule reads. Applying opens
Wellfound's own login-gated flow.
"""

from __future__ import annotations

import json
import re
from typing import Any

from ...data import load_countries
from ...net.browser import BlockedError, browser_session, page_text
from ..models import FetchContext
from .common import collect_pages

_NEXT_DATA = re.compile(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.DOTALL)
_SLUG = re.compile(r"[a-z0-9-]+")
# Seniority words narrow Wellfound's role pages to nothing; the profile rules judge seniority anyway.
_SENIORITY_WORDS = {"junior", "jr", "senior", "sr", "lead", "staff", "principal", "mid", "level", "entry"}
JOB_PREFIX = "JobListingSearchResult:"


def _apollo_state(body: str) -> dict[str, Any]:
    match = _NEXT_DATA.search(body)
    if match is None:
        raise RuntimeError("no listing data on the page; Wellfound may have changed its layout")
    try:
        state = json.loads(match.group(1))["props"]["pageProps"]["apolloState"]["data"]
    except (ValueError, KeyError, TypeError) as exc:
        raise RuntimeError("Wellfound's listing data has an unexpected shape") from exc
    if not isinstance(state, dict):
        raise RuntimeError("Wellfound's listing data has an unexpected shape")
    return state


def _companies_by_job(state: dict[str, Any]) -> dict[str, str]:
    """Job cache key -> company name, from the startups that list the job."""
    owners: dict[str, str] = {}
    for entry in state.values():
        if not isinstance(entry, dict) or entry.get("__typename") != "StartupResult":
            continue
        for ref in entry.get("highlightedJobListings") or []:
            if isinstance(ref, dict) and entry.get("name"):
                owners[ref.get("__ref", "")] = entry["name"]
    return owners


def _salary_text(compensation: Any) -> str | None:
    """Wellfound writes "€60k – €100k • 0.5% – 1.0%"; only the part before the bullet is pay."""
    if not isinstance(compensation, str):
        return None
    return compensation.split("•")[0].strip() or None


def parse_listings(body: str, source_id: str) -> list[dict[str, Any]]:
    state = _apollo_state(body)
    owners = _companies_by_job(state)
    records = []
    for key, job in state.items():
        if not key.startswith(JOB_PREFIX) or not isinstance(job, dict):
            continue
        job_id, slug, title = job.get("id"), str(job.get("slug") or ""), job.get("title")
        if not job_id or not title:
            continue
        url = f"https://wellfound.com/jobs/{job_id}" + (f"-{slug}" if _SLUG.fullmatch(slug) else "")
        accepted = job.get("acceptedRemoteLocationNames")
        records.append(
            {
                "source": source_id,
                "title": title,
                "company": owners.get(key),
                "url": url,
                "apply_url": url,
                "location": ", ".join(str(name) for name in job.get("locationNames") or []),
                "description": job.get("description"),
                "salary": _salary_text(job.get("compensation")),
                "date": job.get("liveStartAt"),
                "remote": job["remote"] if isinstance(job.get("remote"), bool) else None,
                "region_restrictions": accepted if job.get("remote") is True and accepted else None,
            }
        )
    return records


def _listing_url(role: str, location: str, page: int) -> str:
    if not _SLUG.fullmatch(role) or not _SLUG.fullmatch(location):
        raise ValueError(f"role and location must be lowercase slugs, got '{role}' and '{location}'")
    url = f"https://wellfound.com/role/l/{role}/{location}"
    return f"{url}?page={page + 1}" if page else url


def _read_page(fetch: Any, url: str, source_id: str) -> list[dict[str, Any]]:
    page = fetch(url)
    body = page_text(page)
    if page.status >= 400 or (_NEXT_DATA.search(body) is None and "Just a moment" in body):
        raise BlockedError(f"Wellfound blocked the request (HTTP {page.status})")
    return parse_listings(body, source_id)


def role_slug(role: str) -> str:
    """"Senior Full-Stack Engineer (Remote)" -> "full-stack-engineer". Unknown slugs fall back to all roles."""
    words = re.findall(r"[a-z0-9]+", re.sub(r"\(.*?\)", " ", role.lower()))
    return "-".join(word for word in words if word not in _SENIORITY_WORDS)


def locations_for(ctx: FetchContext) -> list[str]:
    catalog = load_countries()
    return [catalog[code]["wellfound"] for code in ctx.countries if catalog.get(code, {}).get("wellfound")]


def fetch(source: dict[str, Any], ctx: FetchContext) -> list[dict[str, Any]]:
    role = role_slug(ctx.role)
    if not role:
        raise ValueError("Wellfound searches by your job title; set one on the Profile page")
    locations = locations_for(ctx)
    if not locations:
        raise ValueError("Wellfound needs target countries; add them on the Profile page")
    pages = max(1, int(source.get("pages", 1)))

    urls = [_listing_url(role, location, page) for location in locations for page in range(pages)]
    with browser_session(source.get("timeout")) as fetch_page:
        return collect_pages(urls, lambda url: _read_page(fetch_page, url, source["id"]))
