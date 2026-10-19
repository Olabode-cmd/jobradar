import json
import re

from scrapling.fetchers import StealthySession

with StealthySession(headless=True, network_idle=True, timeout=90000) as session:
    for url in (
        "https://wellfound.com/role/l/fullstack-product-engineer/germany",
        "https://wellfound.com/role/l/product-engineer/germany",
        "https://wellfound.com/role/l/nurse/canada",
    ):
        try:
            page = session.fetch(url)
            body = page.body.decode("utf8", "replace") if isinstance(page.body, bytes) else str(page.body)
            m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', body, re.S)
            n = 0
            if m:
                st = json.loads(m.group(1))["props"]["pageProps"].get("apolloState", {}).get("data", {})
                n = sum(1 for k in st if k.startswith("JobListingSearchResult"))
            print(page.status, url, "jobs", n, page.css("title::text").get())
        except Exception as exc:
            print("ERR", url, str(exc)[:150])
