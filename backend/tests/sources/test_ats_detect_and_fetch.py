import json
import unittest
from types import SimpleNamespace
from unittest import mock

from app.sources import FetchContext
from app.sources.drivers import ats
from app.sources.drivers.ats import detect_company, tracked_for_provider


class DetectCompanyTests(unittest.TestCase):
    def test_path_based_providers(self):
        cases = {
            "https://boards.greenhouse.io/stripe/jobs/123": ("greenhouse", "stripe"),
            "https://job-boards.greenhouse.io/stripe": ("greenhouse", "stripe"),
            "https://jobs.lever.co/palantir/abc": ("lever", "palantir"),
            "jobs.ashbyhq.com/ashby": ("ashby", "ashby"),
            "https://apply.workable.com/huggingface/": ("workable", "huggingface"),
            "https://jobs.smartrecruiters.com/Visa/743": ("smartrecruiters", "Visa"),
        }
        for url, expected in cases.items():
            with self.subTest(url=url):
                self.assertEqual(detect_company(url), expected)

    def test_subdomain_providers(self):
        cases = {
            "https://bunq.recruitee.com/o/pm": ("recruitee", "bunq"),
            "https://klarna.teamtailor.com/jobs": ("teamtailor", "klarna"),
            "https://personio.jobs.personio.de/": ("personio", "personio"),
            "https://bitly.bamboohr.com/careers": ("bamboohr", "bitly"),
            "https://breezy.breezy.hr/": ("breezy", "breezy"),
        }
        for url, expected in cases.items():
            with self.subTest(url=url):
                self.assertEqual(detect_company(url), expected)

    def test_unknown_or_malformed_urls(self):
        for url in ["https://example.com/careers", "https://boards.greenhouse.io/", "not a url", ""]:
            with self.subTest(url=url):
                self.assertIsNone(detect_company(url))


def ctx(tracked):
    return FetchContext(tracked_companies=tuple(tracked))


class FetchTests(unittest.TestCase):
    def test_tracked_filters_by_provider_enabled_and_valid_slug(self):
        entries = [
            {"name": "A", "provider": "lever", "slug": "a"},
            {"name": "B", "provider": "lever", "slug": "b", "enabled": False},
            {"name": "C", "provider": "greenhouse", "slug": "c"},
            {"name": "D", "provider": "lever", "slug": "../evil"},
            "junk",
        ]
        self.assertEqual([c["slug"] for c in tracked_for_provider(entries, "lever")], ["a"])

    def test_no_tracked_companies_is_an_empty_ok_result(self):
        self.assertEqual(ats.fetch({"id": "lever", "provider": "lever"}, ctx([])), ([], []))

    def test_partial_failure_keeps_good_boards_and_reports_company_errors(self):
        tracked = [{"name": "Good", "provider": "lever", "slug": "good"}, {"name": "Bad", "provider": "lever", "slug": "bad"}]

        def fake_get(url, timeout=None, **_):
            if "/good" in url:
                body = json.dumps([{"text": "Eng", "hostedUrl": "https://jobs.lever.co/good/1"}]).encode()
                return SimpleNamespace(status=200, body=body, json=lambda: json.loads(body))
            return SimpleNamespace(status=404, body=b"", json=lambda: None)

        with mock.patch("app.sources.drivers.ats.fetch.http_get", side_effect=fake_get):
            records, companies = ats.fetch({"id": "lever", "provider": "lever"}, ctx(tracked))
        self.assertEqual(len(records), 1)
        by_key = {c["key"]: c for c in companies}
        self.assertIsNone(by_key["lever:good"]["error"])
        self.assertIn("not found", by_key["lever:bad"]["error"])

    def test_all_boards_failing_raises(self):
        response = SimpleNamespace(status=500, body=b"", json=lambda: None)
        with mock.patch("app.sources.drivers.ats.fetch.http_get", return_value=response), self.assertRaises(RuntimeError):
            ats.fetch({"id": "lever", "provider": "lever"}, ctx([{"name": "Bad", "provider": "lever", "slug": "bad"}]))

    def test_contact_is_sent_with_requests(self):
        seen = {}

        def fake_get(url, timeout=None, **kwargs):
            seen.update(kwargs)
            return SimpleNamespace(status=200, body=b"[]", json=lambda: [])

        context = FetchContext(contact="me@example.com", tracked_companies=({"provider": "lever", "slug": "a"},))
        with mock.patch("app.sources.drivers.ats.fetch.http_get", side_effect=fake_get):
            ats.fetch({"id": "lever", "provider": "lever"}, context)
        self.assertEqual(seen["contact"], "me@example.com")


if __name__ == "__main__":
    unittest.main()
