import json
import sys

from app.data import load_presets
from app.domain.job import normalize_job
from app.sources import FetchContext, fetch_source

NOW = "2026-10-19T00:00:00+00:00"
ctx = FetchContext(role="Fullstack Product Engineer", max_age_days=7)
for source in load_presets():
    if source["id"] not in sys.argv[1:]:
        continue
    result = fetch_source(source, ctx)
    print(source["id"], "error:", result.error, "records:", len(result.records), f"{result.duration_ms}ms")
    for raw in result.records[:4]:
        job = normalize_job(raw, source, NOW)
        print("  ", job["title"], "|", job["company"], "|", job["location_text"], "|", job["apply_url"], "| reloc:", job["offers_relocation"], "| salary:", job["salary_text"], "| remote:", job["remote_status"])
