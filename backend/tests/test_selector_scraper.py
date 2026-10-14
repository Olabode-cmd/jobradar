"""Selector driver tests against a static listing page — no network."""

import unittest
from types import SimpleNamespace
from unittest import mock

from scrapling.parser import Selector

from app.sources.selector_scraper import scrape_listing

LISTING = """
<ul>
  <li class="job">
    <a class="t" href="/jobs/1?utm_source=x"><h2>Frontend <b>Dev</b></h2></a>
    <span class="co"> Acme   Inc </span>
  </li>
  <li class="job">
    <h2>Backend Dev</h2>
    <span class="co">Globex</span>
    <a href="https://jobs.globex.com/2">Apply</a>
  </li>
  <li class="job"><h2>No link here</h2></li>
</ul>
"""

SOURCE = {
    "id": "custom:test",
    "startUrl": "https://example.com/careers",
    "itemSelector": "li.job",
    "fields": {"title": "h2", "company": ".co"},
}


def scrape(source=SOURCE):
    page = Selector(LISTING, url="https://example.com/careers")
    response = SimpleNamespace(status=200, css=page.css, url="https://example.com/careers")
    with mock.patch("app.sources.selector_scraper.http_get", return_value=response):
        return scrape_listing(source)


class SelectorScraperTest(unittest.TestCase):
    def test_plain_selectors_return_clean_text(self):
        first = scrape()[0]
        self.assertEqual(first["title"], "Frontend Dev")
        self.assertEqual(first["company"], "Acme Inc")

    def test_relative_links_become_absolute(self):
        self.assertEqual(scrape()[0]["url"], "https://example.com/jobs/1?utm_source=x")

    def test_absolute_links_are_kept(self):
        self.assertEqual(scrape()[1]["url"], "https://jobs.globex.com/2")

    def test_item_without_link_has_no_url(self):
        self.assertIsNone(scrape()[2]["url"])

    def test_pseudo_element_selectors_are_respected(self):
        source = {**SOURCE, "fields": {"title": "h2::text", "url": "a::attr(href)"}}
        self.assertEqual(scrape(source)[1]["url"], "https://jobs.globex.com/2")

    def test_missing_config_raises(self):
        with self.assertRaises(ValueError):
            scrape_listing({"id": "x"})


if __name__ == "__main__":
    unittest.main()
