import copy
import sys

from app.data import load_presets
from app.domain.job import normalize_job
from app.domain.relocation import job_offers_relocation
from app.sources import FetchContext, fetch_source

NOW = "2026-10-19T00:00:00+00:00"
ctx = FetchContext(role="Fullstack Product Engineer", max_age_days=7)
for source in load_presets():
    if source["id"] not in sys.argv[1:]:
        continue
    source = copy.deepcopy(source)
    if source["id"] == "indeed":
        source["pages"] = 2
        source["searches"] = source["searches"][:2] + source["searches"][2:]
    if source["id"] == "wellfound":
        source["roles"] = ["software-engineer"]
    result = fetch_source(source, ctx)
    print(source["id"], "error:", result.error, "records:", len(result.records), f"{result.duration_ms}ms")
    by_host = {}
    for raw in result.records:
        job = normalize_job(raw, source, NOW)
        key = raw["url"].split("/")[2]
        by_host[key] = by_host.get(key, 0) + 1
    print("  per host:", by_host)
    relocating = 0
    for raw in result.records:
        job = normalize_job(raw, source, NOW)
        if job_offers_relocation(job):
            relocating += 1
            print("   RELOC:", job["title"], "|", job["company"], "|", job["location_text"], "|", job["salary_text"], "|", job["apply_url"])
    print("  mention relocation:", relocating, "of", len(result.records))
    for raw in result.records[:2]:
        job = normalize_job(raw, source, NOW)
        print("  sample:", job["title"], "|", job["company"], "|", job["location_text"], "|", job["posted_at"], "|", job["salary_text"], "| remote:", job["remote_status"])
