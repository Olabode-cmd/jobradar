import sys

from scrapling.fetchers import StealthyFetcher

url, out = sys.argv[1], sys.argv[2]
page = StealthyFetcher.fetch(url, headless=True, network_idle=True, timeout=90000, disable_resources=False)
body = page.body.decode("utf-8", "replace") if isinstance(page.body, bytes) else str(page.body)
open(out, "w", encoding="utf-8").write(body)
print("status", page.status, "len", len(body), "url", page.url)
print("title", page.css("title::text").get())
