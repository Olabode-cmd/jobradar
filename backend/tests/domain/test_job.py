import json
import unittest

from app.domain.job import infer_remote, is_usable, normalize_job
from tests.support import BOARD, NOW, raw_job


class IsUsableTests(unittest.TestCase):
    def test_needs_title_and_link(self):
        self.assertTrue(is_usable(raw_job()))
        self.assertFalse(is_usable(raw_job(url="")))
        self.assertFalse(is_usable(raw_job(title="")))
        self.assertFalse(is_usable({"last_updated": 1, "legal": "terms"}))


class InferRemoteTests(unittest.TestCase):
    def test_explicit_flag_wins(self):
        self.assertFalse(infer_remote({"remote": False, "location": "Remote"}))

    def test_location_title_and_tags_are_read_but_not_description(self):
        self.assertTrue(infer_remote({"location": "Remote - EU"}))
        self.assertIsNone(infer_remote({"location": "Berlin", "description": "remote work is possible"}))


class NormalizeJobTests(unittest.TestCase):
    def test_maps_the_record(self):
        job = normalize_job(raw_job(date=1760428800), BOARD, NOW)
        self.assertEqual(job["posted_at"], "2025-10-14T08:00:00+00:00")
        self.assertEqual(job["description"], "React and TypeScript")
        self.assertEqual(job["remote_status"], "remote")
        self.assertEqual(job["canonical_url"], "https://jobs.example.com/1")

    def test_missing_date_falls_back_to_first_seen(self):
        job = normalize_job(raw_job(date=None), BOARD, NOW)
        self.assertEqual(job["posted_at"], job["first_seen_at"])

    def test_emails_extracted_from_description_and_stored_as_json(self):
        job = normalize_job(raw_job(description='<p>Write to <a href="mailto:careers@acme.com">us</a></p>'), BOARD, NOW)
        self.assertEqual(json.loads(job["emails"]), ["careers@acme.com"])

    def test_given_email_list_is_kept(self):
        job = normalize_job(raw_job(emails=["a@b.co", "c@d.co"]), BOARD, NOW)
        self.assertEqual(json.loads(job["emails"]), ["a@b.co", "c@d.co"])

    def test_apply_method_detected_from_host(self):
        job = normalize_job(raw_job(url="https://jobs.lever.co/acme/1"), BOARD, NOW)
        self.assertEqual(job["apply_method"], "ats")

    def test_repairs_mojibake_in_title_and_company(self):
        job = normalize_job(raw_job(title="Dev \u00e2\u0080\u0094 Remote", company="Caf\u00c3\u00a9"), BOARD, NOW)
        self.assertEqual((job["title"], job["company"]), ("Dev \u2014 Remote", "Caf\u00e9"))


if __name__ == "__main__":
    unittest.main()
