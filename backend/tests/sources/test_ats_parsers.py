"""One test per provider, using fixtures shaped like the real responses."""

import unittest
import xml.etree.ElementTree as ET

from app.domain.job import normalize_job
from app.sources.drivers.ats import PROVIDERS
from tests.support import NOW

COMPANY = {"name": "Acme", "slug": "acme", "provider": "x"}


def parse(provider, payload):
    records = PROVIDERS[provider].parse(payload, COMPANY)
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
        self.assertEqual((job["description"], job["company_id"]), ("Who we are", "acme"))

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


if __name__ == "__main__":
    unittest.main()
