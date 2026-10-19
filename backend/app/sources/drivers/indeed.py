"""Indeed (Tier C): logged-out search result pages, one per country host.

Indeed protects every page with Cloudflare, so this needs the stealth browser, and expect it to
break. Result cards are read from the JSON Indeed embeds for its own front end, not from CSS
classes, which are generated and change often. Listing pages load; detail pages are blocked, so
relocation can only be judged from the snippet Indeed shows on the result card.
"""

from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import urlencode

from ...data import load_countries
from ...net.browser import BlockedError, browser_session, page_text
from ..models import FetchContext
from .common import collect_pages

RELOCATION_QUERY_SUFFIX = " relocation"
# Indeed's "posted within" filter only accepts these day counts.
FROMAGE_DAYS = (1, 3, 7, 14)
_RESULTS_MARKER = re.compile(r'window\.mosaic\.providerData\["mosaic-provider-jobcards"\]\s*=\s*')
_REMOTE_LOCATION = re.compile(r"home ?office|remote|telearbeit|télétravail|在宅|リモート", re.IGNORECASE)
_CURRENCY_BY_COUNTRY = {"DE": "EUR", "NL": "EUR", "CA": "CAD", "JP": "JPY"}
_SALARY_PERIODS = {"YEARLY": "per year", "MONTHLY": "per month", "WEEKLY": "per week", "DAILY": "per day", "HOURLY": "per hour"}


def _fromage(max_age_days: int | None) -> int | None:
    if not max_age_days or max_age_days < 1:
        return None
    return next((days for days in FROMAGE_DAYS if days >= max_age_days), None)


def _search_url(host: str, location: str, query: str, max_age_days: int | None, page: int) -> str:
    if not re.fullmatch(r"[a-z0-9.-]+\.indeed\.com", host):
        raise ValueError(f"'{host}' is not an Indeed host")
    params: dict[str, Any] = {"q": query, "l": location, "sort": "date"}
    if (fromage := _fromage(max_age_days)) is not None:
        params["fromage"] = fromage
    if page:
        params["start"] = page * 10
    return f"https://{host}/jobs?{urlencode(params)}"


def parse_results(body: str) -> list[dict[str, Any]]:
    """The raw result objects embedded in a search page. Raises if the page has none."""
    marker = _RESULTS_MARKER.search(body)
    if marker is None:
        raise RuntimeError("no results data on the page; Indeed may have changed its layout")
    try:
        data, _ = json.JSONDecoder().raw_decode(body, marker.end())
        results = data["metaData"]["mosaicProviderJobCardsModel"]["results"]
    except (ValueError, KeyError, TypeError) as exc:
        raise RuntimeError("Indeed's results data has an unexpected shape") from exc
    if not isinstance(results, list):
        raise RuntimeError("Indeed's results data has an unexpected shape")
    return [item for item in results if isinstance(item, dict)]


def _number(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else f"{value:.2f}"


def _salary_text(item: dict[str, Any]) -> str | None:
    salary = item.get("extractedSalary")
    if not isinstance(salary, dict):
        return None
    low, high = salary.get("min"), salary.get("max")
    if not isinstance(low, (int, float)) and not isinstance(high, (int, float)):
        return None
    if not low and not high:
        return None
    amount = f"{_number(low)}–{_number(high)}" if low and high and low != high else _number(high or low)
    currency = _CURRENCY_BY_COUNTRY.get(str(item.get("country") or "").upper(), "")
    period = _SALARY_PERIODS.get(str(salary.get("type") or "").upper(), "")
    return " ".join(part for part in (currency, amount, period) if part)


def to_record(item: dict[str, Any], source_id: str, host: str) -> dict[str, Any] | None:
    key = item.get("jobkey")
    title = item.get("displayTitle") or item.get("title")
    if not key or not title:
        return None
    location = item.get("formattedLocation") or ""
    url = f"https://{host}/viewjob?jk={key}"
    return {
        "source": source_id,
        "title": title,
        "company": item.get("company") or item.get("truncatedCompany"),
        "url": url,
        "apply_url": url,
        "location": location,
        "description": item.get("snippet"),
        "salary": _salary_text(item),
        "date": item.get("pubDate") or item.get("createDate"),
        "remote": True if item.get("remoteLocation") or _REMOTE_LOCATION.search(location) else None,
    }


def _read_page(fetch: Any, url: str, source_id: str, host: str) -> list[dict[str, Any]]:
    page = fetch(url)
    body = page_text(page)
    if page.status >= 400 or (_RESULTS_MARKER.search(body) is None and "Just a moment" in body):
        raise BlockedError(f"Indeed blocked the request (HTTP {page.status}) for {host}")
    return [record for item in parse_results(body) if (record := to_record(item, source_id, host))]


def searches_for(ctx: FetchContext) -> list[dict[str, str]]:
    """One Indeed search per target country the catalog maps to an Indeed host."""
    catalog = load_countries()
    return [catalog[code]["indeed"] for code in ctx.countries if catalog.get(code, {}).get("indeed")]


def build_query(ctx: FetchContext) -> str:
    if not ctx.role:
        raise ValueError("Indeed searches by your job title; set one on the Profile page")
    # Asking Indeed for "relocation" up front keeps the scarce result slots for postings that mention it.
    return ctx.role + (RELOCATION_QUERY_SUFFIX if ctx.open_to_relocation else "")


def fetch(source: dict[str, Any], ctx: FetchContext) -> list[dict[str, Any]]:
    query = build_query(ctx)
    searches = searches_for(ctx)
    if not searches:
        raise ValueError("Indeed needs target countries; add them on the Profile page")
    pages = max(1, int(source.get("pages", 1)))

    targets = [
        (_search_url(search["host"], search["location"], query, ctx.max_age_days, page), search["host"])
        for search in searches
        for page in range(pages)
    ]
    with browser_session(source.get("timeout")) as fetch_page:
        return collect_pages(targets, lambda target: _read_page(fetch_page, target[0], source["id"], target[1]))
