import json
import unittest
from contextlib import contextmanager
from types import SimpleNamespace
from unittest import mock

from app.sources import FetchContext
from app.sources.drivers import indeed, selector, wellfound

CTX = FetchContext(role="Senior Data Analyst", countries=("DE", "JP"), max_age_days=7, open_to_relocation=True)

INDEED_PAGE = (
    "<script>window.mosaic.providerData[\"mosaic-provider-jobcards\"]="
    + json.dumps({"metaData": {"mosaicProviderJobCardsModel": {"results": [{
        "jobkey": "abc123", "displayTitle": "Data Analyst", "company": "Acme GmbH", "formattedLocation": "Berlin",
        "snippet": "<li>Relocation package included</li>", "pubDate": 1791954000000, "country": "DE",
        "extractedSalary": {"min": 54000, "max": 72000, "type": "YEARLY"},
    }]}}})
    + ";\n</script>"
)

WELLFOUND_PAGE = '<script id="__NEXT_DATA__" type="application/json">' + json.dumps({"props": {"pageProps": {"apolloState": {"data": {
    "JobListingSearchResult:1": {"__typename": "JobListingSearchResult", "id": "1", "slug": "data-analyst", "title": "Data Analyst",
                                 "description": "Relocation support if you move to Berlin", "locationNames": ["Berlin"],
                                 "remote": False, "compensation": "€60k – €80k • 0.1%", "liveStartAt": 1791954000},
    "StartupResult:9": {"__typename": "StartupResult", "name": "Acme", "highlightedJobListings": [{"__ref": "JobListingSearchResult:1"}]},
}}}}}) + "</script>"


def fake_browser(body, seen):
    @contextmanager
    def session(timeout=None):
        def fetch(url):
            seen.append(url)
            return SimpleNamespace(status=200, body=body)
        yield fetch
    return session


class IndeedTests(unittest.TestCase):
    def test_searches_come_from_the_profile(self):
        seen = []
        with mock.patch.object(indeed, "browser_session", fake_browser(INDEED_PAGE, seen)):
            records = indeed.fetch({"id": "indeed"}, CTX)
        self.assertEqual(len(seen), 2)
        self.assertTrue(seen[0].startswith("https://de.indeed.com/jobs?q=Senior+Data+Analyst+relocation"))
        self.assertIn("fromage=7", seen[0])
        self.assertTrue(seen[1].startswith("https://jp.indeed.com/"))
        self.assertEqual(records[0]["url"], "https://de.indeed.com/viewjob?jk=abc123")
        self.assertEqual(records[0]["salary"], "EUR 54000–72000 per year")

    def test_relocation_word_is_only_added_when_open_to_it(self):
        self.assertEqual(indeed.build_query(FetchContext(role="Nurse")), "Nurse")

    def test_without_a_role_or_countries_nothing_is_fetched(self):
        seen = []
        with mock.patch.object(indeed, "browser_session", fake_browser(INDEED_PAGE, seen)):
            for ctx in (FetchContext(countries=("DE",)), FetchContext(role="Nurse")):
                with self.subTest(ctx=ctx), self.assertRaises(ValueError):
                    indeed.fetch({"id": "indeed"}, ctx)
        self.assertEqual(seen, [])

    def test_one_blocked_country_does_not_lose_the_others(self):
        pages = iter([SimpleNamespace(status=403, body="Just a moment..."), SimpleNamespace(status=200, body=INDEED_PAGE)])

        @contextmanager
        def session(timeout=None):
            yield lambda url: next(pages)

        with mock.patch.object(indeed, "browser_session", session):
            self.assertEqual(len(indeed.fetch({"id": "indeed"}, CTX)), 1)


class WellfoundTests(unittest.TestCase):
    def test_role_slug_drops_seniority_and_punctuation(self):
        self.assertEqual(wellfound.role_slug("Senior Full-Stack Engineer (Remote)"), "full-stack-engineer")
        self.assertEqual(wellfound.role_slug("Nurse"), "nurse")

    def test_urls_come_from_the_profile_and_jobs_join_their_company(self):
        seen = []
        with mock.patch.object(wellfound, "browser_session", fake_browser(WELLFOUND_PAGE, seen)):
            records = wellfound.fetch({"id": "wellfound"}, CTX)
        self.assertEqual(seen[0], "https://wellfound.com/role/l/data-analyst/germany")
        self.assertEqual(seen[1], "https://wellfound.com/role/l/data-analyst/japan")
        first = records[0]
        self.assertEqual((first["company"], first["salary"], first["remote"]), ("Acme", "€60k – €80k", False))
        self.assertEqual(first["url"], "https://wellfound.com/jobs/1-data-analyst")


class CountrySelectorTests(unittest.TestCase):
    def test_country_template_expands_per_target_country(self):
        source = {"id": "relocateme", "startUrl": "https://relocate.me/x?country%5B%5D={country}",
                  "countryKey": "relocateme", "itemSelector": "li"}
        self.assertEqual(selector._country_urls(source, FetchContext(countries=("NL", "UK"))), [
            "https://relocate.me/x?country%5B%5D=Netherlands",
            "https://relocate.me/x?country%5B%5D=United%20Kingdom",
        ])
        with self.assertRaises(ValueError):
            selector._country_urls(source, FetchContext())


if __name__ == "__main__":
    unittest.main()
