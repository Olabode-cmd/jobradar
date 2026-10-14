"""ATS parsers, URL detection and board field mapping, using fixtures shaped like real responses."""

import json
import unittest
import xml.etree.ElementTree as ET
from types import SimpleNamespace
from unittest import mock

from app.normalize import normalize_job
from app.sources import drivers
from app.sources.ats import PROVIDERS, detect_company, fetch_ats, tracked_for_provider
from app.sources.hackernews import _parse_comment

COMPANY = {"name": "Acme", "slug": "acme", "provider": "x"}
NOW = "2026-10-14T00:00:00+00:00"


def parse(provider, payload, company=COMPANY):
    records = PROVIDERS[provider].parse(payload, company)
    assert records, f"{provider} produced no records"
    return records[0]


class ParserTests(unittest.TestCase):
    def test_greenhouse_unescapes_content_and_uses_board_company_name(self):
        payload = {"jobs": [{
            "title": "Abuse Investigator", "company_name": "Stripe",
            "absolute_url": "https://stripe.com/jobs/search?gh_jid=8172510",
            "location": {"name": "Seattle"}, "content": "&lt;p&gt;Who we are&lt;/p&gt;",
            "first_published": "2026-09-09T10:50:29-04:00",
        }]}
        record = parse("greenhouse", payload)
        self.assertEqual((record["company"], record["location"]), ("Stripe", "Seattle"))
        job = normalize_job(record, {"id": "greenhouse"}, NOW)
        self.assertEqual(job["description"], "Who we are")
        self.assertEqual(job["company_id"], "acme")

    def test_lever_epoch_milliseconds_and_remote_workplace(self):
        payload = [{"text": "Engineer", "hostedUrl": "https://jobs.lever.co/acme/1", "applyUrl": "https://jobs.lever.co/acme/1/apply",
                    "categories": {"location": "Remote"}, "descriptionPlain": "Hi", "createdAt": 1786469891368, "workplaceType": "remote"}]
        record = parse("lever", payload)
        job = normalize_job(record, {"id": "lever"}, NOW)
        self.assertTrue(job["posted_at"].startswith("2026-"))
        self.assertEqual(job["remote_status"], "remote")
        self.assertEqual(record["apply_url"], "https://jobs.lever.co/acme/1/apply")

    def test_ashby_skips_unlisted_and_keeps_compensation(self):
        payload = {"jobs": [
            {"title": "Hidden", "isListed": False, "jobUrl": "https://jobs.ashbyhq.com/acme/0"},
            {"title": "EM", "isListed": True, "jobUrl": "https://jobs.ashbyhq.com/acme/1", "isRemote": True,
             "location": "Remote - EU", "compensation": {"compensationTierSummary": "€110K – €185K"}},
        ]}
        records = PROVIDERS["ashby"].parse(payload, COMPANY)
        self.assertEqual([r["title"] for r in records], ["EM"])
        self.assertEqual(records[0]["salary"], "€110K – €185K")

    def test_workable_builds_location_and_remote(self):
        payload = {"name": "Hugging Face", "jobs": [{"title": "MLE", "url": "https://apply.workable.com/j/ABC", "city": "Paris",
                   "country": "France", "telecommuting": True, "published_on": "2026-05-29"}]}
        record = parse("workable", payload)
        self.assertEqual((record["company"], record["location"], record["remote"]), ("Hugging Face", "Paris, France", True))

    def test_recruitee_converts_utc_suffix_and_skips_unpublished(self):
        payload = {"offers": [
            {"title": "Draft", "status": "draft", "careers_url": "https://x.recruitee.com/o/draft"},
            {"title": "PO", "status": "published", "careers_url": "https://careers.bunq.com/o/po", "company_name": "bunq",
             "published_at": "2026-10-13 10:58:56 UTC", "location": "Amsterdam", "remote": False, "description": "<p>Hi</p>"},
        ]}
        records = PROVIDERS["recruitee"].parse(payload, COMPANY)
        self.assertEqual(len(records), 1)
        self.assertEqual(normalize_job(records[0], {"id": "recruitee"}, NOW)["posted_at"], "2026-10-13T10:58:56+00:00")

    def test_smartrecruiters_builds_public_url(self):
        payload = {"content": [{"id": "743", "name": "Analyst", "releasedDate": "2026-10-01T00:00:00Z",
                                "company": {"identifier": "Visa"}, "location": {"city": "Berlin", "country": "de", "remote": False}}]}
        self.assertEqual(parse("smartrecruiters", payload)["url"], "https://jobs.smartrecruiters.com/Visa/743")

    def test_teamtailor_rss(self):
        root = ET.fromstring("<rss><channel><item><title> Designer </title><link>https://acme.teamtailor.com/jobs/1</link>"
                             "<description>Hi</description><pubDate>Tue, 14 Oct 2026 08:00:00 +0000</pubDate></item></channel></rss>")
        record = parse("teamtailor", root)
        self.assertEqual((record["title"], record["url"]), ("Designer", "https://acme.teamtailor.com/jobs/1"))

    def test_personio_xml(self):
        root = ET.fromstring(
            "<workzag-jobs><position><id>1834171</id><subcompany>Personio SE</subcompany><office>Munich</office>"
            "<name>PM</name><createdAt>2026-10-01T09:00:00+00:00</createdAt><jobDescriptions><jobDescription>"
            "<name>Tasks</name><value>&lt;p&gt;Plan&lt;/p&gt;</value></jobDescription></jobDescriptions></position></workzag-jobs>")
        record = parse("personio", root)
        self.assertEqual(record["url"], "https://acme.jobs.personio.de/job/1834171")
        self.assertEqual(record["company"], "Personio SE")

    def test_bamboohr_builds_url_and_location(self):
        payload = {"result": [{"id": "8", "jobOpeningName": "Director", "location": {"city": "Boston", "state": "MA"},
                               "atsLocation": {"country": "United States"}, "isRemote": None}]}
        record = parse("bamboohr", payload)
        self.assertEqual(record["url"], "https://acme.bamboohr.com/careers/8")
        self.assertEqual(record["location"], "Boston, MA, United States")

    def test_breezy_uses_nested_company_and_location(self):
        payload = [{"name": "Dev", "url": "https://acme.breezy.hr/p/1", "published_date": "2024-02-15T14:37:22.684Z",
                    "location": {"name": "Remote", "is_remote": True}, "company": {"name": "MS Breezy"}}]
        record = parse("breezy", payload)
        self.assertEqual((record["company"], record["remote"]), ("MS Breezy", True))


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


class FetchAtsTests(unittest.TestCase):
    def config(self, tracked):
        return SimpleNamespace(companies={"tracked": tracked})

    def test_tracked_filters_by_provider_enabled_and_valid_slug(self):
        config = self.config([
            {"name": "A", "provider": "lever", "slug": "a"},
            {"name": "B", "provider": "lever", "slug": "b", "enabled": False},
            {"name": "C", "provider": "greenhouse", "slug": "c"},
            {"name": "D", "provider": "lever", "slug": "../evil"},
            "junk",
        ])
        self.assertEqual([c["slug"] for c in tracked_for_provider(config, "lever")], ["a"])

    def test_no_tracked_companies_is_an_empty_ok_result(self):
        self.assertEqual(fetch_ats({"id": "lever", "provider": "lever"}, self.config([])), ([], []))

    def test_partial_failure_keeps_good_boards_and_reports_company_errors(self):
        config = self.config([{"name": "Good", "provider": "lever", "slug": "good"}, {"name": "Bad", "provider": "lever", "slug": "bad"}])

        def fake_get(url, timeout=None):
            if "/good" in url:
                body = json.dumps([{"text": "Eng", "hostedUrl": "https://jobs.lever.co/good/1"}]).encode()
                return SimpleNamespace(status=200, body=body, json=lambda: json.loads(body))
            return SimpleNamespace(status=404, body=b"", json=lambda: None)

        with mock.patch("app.sources.ats.http_get", side_effect=fake_get):
            records, companies = fetch_ats({"id": "lever", "provider": "lever"}, config)
        self.assertEqual(len(records), 1)
        by_key = {c["key"]: c for c in companies}
        self.assertIsNone(by_key["lever:good"]["error"])
        self.assertIn("not found", by_key["lever:bad"]["error"])

    def test_all_boards_failing_raises(self):
        config = self.config([{"name": "Bad", "provider": "lever", "slug": "bad"}])
        response = SimpleNamespace(status=500, body=b"", json=lambda: None)
        with mock.patch("app.sources.ats.http_get", return_value=response), self.assertRaises(RuntimeError):
            fetch_ats({"id": "lever", "provider": "lever"}, config)


class BoardMappingTests(unittest.TestCase):
    def fetch(self, source, payload):
        response = SimpleNamespace(status=200, json=lambda: payload)
        with mock.patch.object(drivers, "_http_get", return_value=response):
            return drivers._fetch_json({"timeout": 5, **source})

    def test_jobicy_field_names_and_salary(self):
        source = {"id": "jobicy", "startUrl": "x", "allRemote": True}
        record = self.fetch(source, {"jobs": [{"url": "https://jobicy.com/jobs/1", "jobTitle": "Director", "companyName": "MaintainX",
                                              "jobGeo": "Canada", "jobDescription": "<p>Hi</p>", "pubDate": "2026-10-14T04:48:41+00:00",
                                              "salaryMin": 213500, "salaryMax": 390000, "salaryCurrency": "USD", "salaryPeriod": "yearly"}]})[0]
        self.assertEqual((record["title"], record["company"], record["remote"]), ("Director", "MaintainX", True))
        self.assertEqual(record["salary"], "USD 213500–390000 yearly")

    def test_himalayas_guid_epoch_and_restrictions(self):
        source = {"id": "himalayas", "startUrl": "x", "allRemote": True}
        record = self.fetch(source, {"jobs": [{"title": "Architect", "companyName": "Rubicon", "guid": "https://himalayas.app/j/1",
                                              "pubDate": 1791972759, "locationRestrictions": ["Canada"]}]})[0]
        self.assertEqual(record["url"], "https://himalayas.app/j/1")
        self.assertEqual(record["region_restrictions"], ["Canada"])
        self.assertTrue(normalize_job(record, source, NOW)["posted_at"].startswith("2026-"))

    def test_arbeitnow_explicit_false_remote_is_respected(self):
        source = {"id": "arbeitnow", "startUrl": "x"}
        record = self.fetch(source, {"data": [{"title": "SAP", "company_name": "Sidekick", "url": "https://a.example/1", "remote": False,
                                              "location": "Bonn", "created_at": 1791973862}]})[0]
        self.assertIs(record["remote"], False)
        self.assertIsNone(normalize_job(record, source, NOW)["remote_status"])


class HackerNewsTests(unittest.TestCase):
    def test_parses_pipe_header_and_marks_low_confidence(self):
        comment = {"objectID": "99", "created_at": "2026-10-01T00:00:00Z",
                   "comment_text": 'Acme | Senior Backend Engineer | Berlin | REMOTE<p>Apply <a href="https://acme.example/jobs/1">here</a> or jobs@acme.example'}
        record = _parse_comment(comment, "hackernews")
        self.assertEqual((record["company"], record["title"], record["remote"]), ("Acme", "Senior Backend Engineer", True))
        self.assertEqual(record["apply_url"], "https://acme.example/jobs/1")
        self.assertTrue(record["low_confidence"])

    def test_non_job_comments_are_ignored(self):
        self.assertIsNone(_parse_comment({"objectID": "1", "comment_text": "Thanks for posting!"}, "hackernews"))


if __name__ == "__main__":
    unittest.main()
