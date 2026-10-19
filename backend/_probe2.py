import json
import re
import urllib.request

from scrapling.fetchers import StealthySession

for host in ("https://relocate.me", "https://japan-dev.com"):
    req = urllib.request.Request(host + "/robots.txt", headers={"User-Agent": "Mozilla/5.0"})
    text = urllib.request.urlopen(req, timeout=20).read().decode("utf8", "replace")
    print(host, "robots:", [line for line in text.splitlines() if line.lower().startswith(("user-agent", "disallow", "crawl"))][:12])

t = open("backend/_wf_nl.html", encoding="utf-8").read()
st = json.loads(re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', t, re.S).group(1))["props"]["pageProps"]["apolloState"]["data"]
jobs = {k: v for k, v in st.items() if k.startswith("JobListingSearchResult")}
linked = set()
for v in st.values():
    if v.get("__typename") == "StartupResult":
        linked.update(ref["__ref"] for ref in v.get("highlightedJobListings", []))
print("wellfound NL jobs", len(jobs), "linked to a startup", len(linked & set(jobs)))
import datetime
print("liveStartAt years", sorted({datetime.datetime.fromtimestamp(j["liveStartAt"]).strftime("%Y-%m") for j in jobs.values()}))

with StealthySession(headless=True, network_idle=True, timeout=90000) as session:
    for url in (
        "https://nl.indeed.com/jobs?q=software+engineer+relocation&l=Nederland&sort=date",
        "https://ca.indeed.com/jobs?q=software+engineer+relocation&l=Canada&sort=date",
        "https://jp.indeed.com/jobs?q=software+engineer+relocation&l=Japan&sort=date",
        "https://wellfound.com/role/l/full-stack-engineer/germany",
        "https://wellfound.com/role/l/frontend-engineer/canada",
    ):
        try:
            page = session.fetch(url)
            body = page.body.decode("utf8", "replace") if isinstance(page.body, bytes) else str(page.body)
            has_indeed = "mosaic-provider-jobcards" in body
            has_wf = "__NEXT_DATA__" in body
            print(page.status, url, "indeed-data" if has_indeed else "", "wf-data" if has_wf else "", page.css("title::text").get())
        except Exception as exc:
            print("ERR", url, str(exc)[:120])
