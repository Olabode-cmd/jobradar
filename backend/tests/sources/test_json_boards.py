import unittest
from types import SimpleNamespace
from unittest import mock

from app.domain.job import normalize_job
from app.sources import FetchContext
from app.sources.drivers import hackernews, json_board
from tests.support import NOW


def fetch(source, payload):
    response = SimpleNamespace(status=200, json=lambda: payload)
    with mock.patch.object(json_board, "http_get", return_value=response):
        return json_board.fetch({"timeout": 5, **source}, FetchContext())


class JsonBoardTests(unittest.TestCase):
    def test_jobicy_field_names_and_salary(self):
        source = {"id": "jobicy", "startUrl": "x", "allRemote": True}
        record = fetch(source, {"jobs": [{
            "url": "https://jobicy.com/jobs/1", "jobTitle": "Director", "companyName": "MaintainX", "jobGeo": "Canada",
            "jobDescription": "<p>Hi</p>", "pubDate": "2026-10-14T04:48:41+00:00",
            "salaryMin": 213500, "salaryMax": 390000, "salaryCurrency": "USD", "salaryPeriod": "yearly",
        }]})[0]
        self.assertEqual((record["title"], record["company"], record["remote"]), ("Director", "MaintainX", True))
        self.assertEqual(record["salary"], "USD 213500–390000 yearly")

    def test_himalayas_guid_epoch_and_restrictions(self):
        source = {"id": "himalayas", "startUrl": "x", "allRemote": True}
        record = fetch(source, {"jobs": [{
            "title": "Architect", "companyName": "Rubicon", "guid": "https://himalayas.app/j/1",
            "pubDate": 1791972759, "locationRestrictions": ["Canada"],
        }]})[0]
        self.assertEqual(record["url"], "https://himalayas.app/j/1")
        self.assertEqual(record["region_restrictions"], ["Canada"])
        self.assertTrue(normalize_job(record, source, NOW)["posted_at"].startswith("2026-"))

    def test_arbeitnow_explicit_false_remote_is_respected(self):
        source = {"id": "arbeitnow", "startUrl": "x"}
        record = fetch(source, {"data": [{
            "title": "SAP", "company_name": "Sidekick", "url": "https://a.example/1", "remote": False,
            "location": "Bonn", "created_at": 1791973862,
        }]})[0]
        self.assertIs(record["remote"], False)
        self.assertIsNone(normalize_job(record, source, NOW)["remote_status"])

    def test_remoteok_style_list_payload(self):
        record = fetch({"id": "remoteok", "startUrl": "x", "allRemote": True},
                       [{"legal": "terms"}, {"position": "Dev", "company": "Acme", "url": "https://r.example/1", "epoch": 1791973862}])[1]
        self.assertEqual((record["title"], record["company"]), ("Dev", "Acme"))

    def test_unexpected_shape_raises(self):
        with self.assertRaises(RuntimeError):
            fetch({"id": "x", "startUrl": "x"}, {"jobs": "nope"})

    def test_http_errors_raise(self):
        response = SimpleNamespace(status=503, json=lambda: None)
        with mock.patch.object(json_board, "http_get", return_value=response), self.assertRaises(RuntimeError):
            json_board.fetch({"id": "x", "startUrl": "x"}, FetchContext())


class HackerNewsTests(unittest.TestCase):
    def test_parses_pipe_header_and_marks_low_confidence(self):
        comment = {"objectID": "99", "created_at": "2026-10-01T00:00:00Z",
                   "comment_text": 'Acme | Senior Backend Engineer | Berlin | REMOTE<p>Apply <a href="https://acme.example/jobs/1">here</a> or jobs@acme.example'}
        record = hackernews.parse_comment(comment, "hackernews")
        self.assertEqual((record["company"], record["title"], record["remote"]), ("Acme", "Senior Backend Engineer", True))
        self.assertEqual(record["apply_url"], "https://acme.example/jobs/1")
        self.assertTrue(record["low_confidence"])

    def test_non_job_comments_are_ignored(self):
        self.assertIsNone(hackernews.parse_comment({"objectID": "1", "comment_text": "Thanks for posting!"}, "hackernews"))


if __name__ == "__main__":
    unittest.main()
