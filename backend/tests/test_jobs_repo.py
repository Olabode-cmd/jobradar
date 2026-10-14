"""Jobs repository tests against a temp SQLite file — no network."""

import os
import tempfile
import unittest

from app import jobs_repo
from app.db import open_db
from app.jobs_repo import JobFilters
from app.pipeline import process_batch

PROFILE = {"role": "Engineer", "includeKeywords": ["react"], "remoteOnly": False, "maxAgeDays": None}
SOURCE = {"id": "board", "tier": "A", "kind": "board", "type": "api"}
NOW = "2026-10-14T00:00:00+00:00"


def raw(n, title, company="Stripe", **extra):
    return {
        "title": title,
        "company": company,
        "url": f"https://jobs.example.com/{n}",
        "description": "<p>React and TypeScript</p>",
        "date": "2026-10-10T00:00:00+00:00",
        "remote": True,
        **extra,
    }


class JobsRepoTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        os.environ["JOBRADAR_DB"] = self.tmp.name
        self.conn = open_db()
        process_batch(
            self.conn,
            [
                raw(1, "React Engineer"),
                raw(2, "Vue Engineer", company="Globex"),
                raw(3, "Plumber", company="Pipes Ltd", description="Pipes", remote=False),
            ],
            SOURCE, PROFILE, set(), set(), {}, {}, NOW, dry_run=False,
        )

    def tearDown(self):
        self.conn.close()
        os.unlink(self.tmp.name)
        os.environ.pop("JOBRADAR_DB", None)

    def test_default_filter_hides_restricted_and_orders_by_score(self):
        self.conn.execute("UPDATE jobs SET eligibility = 'restricted' WHERE id = 3")
        items, total = jobs_repo.list_jobs(self.conn, JobFilters())
        self.assertEqual(total, 2)
        self.assertEqual(items[0]["title"], "React Engineer")

    def test_search_matches_title_and_company_and_escapes_wildcards(self):
        self.assertEqual(jobs_repo.list_jobs(self.conn, JobFilters(query="globex"))[1], 1)
        self.assertEqual(jobs_repo.list_jobs(self.conn, JobFilters(query="%"))[1], 0)

    def test_remote_and_source_filters(self):
        _, remote_total = jobs_repo.list_jobs(self.conn, JobFilters(remote_only=True, eligibility=()))
        self.assertEqual(remote_total, 2)
        _, other = jobs_repo.list_jobs(self.conn, JobFilters(source="nope", eligibility=()))
        self.assertEqual(other, 0)

    def test_detail_has_text_description_and_source_links(self):
        job = jobs_repo.get_job(self.conn, 1)
        self.assertEqual(job["description"], "React and TypeScript")
        self.assertEqual(job["source_links"][0]["source_id"], "board")
        self.assertTrue(job["score_reasons"])

    def test_source_listed_once_even_with_several_urls(self):
        self.conn.execute(
            "INSERT INTO job_sources (job_id, source_id, url, seen_at) VALUES (1, 'board', 'https://alt.example.com/1', ?)",
            (NOW,),
        )
        items, _ = jobs_repo.list_jobs(self.conn, JobFilters(query="React"))
        self.assertEqual(items[0]["sources"], ["board"])

    def test_status_update_sets_timestamps_and_clears_repost_flag(self):
        self.conn.execute("UPDATE jobs SET reposted = 1 WHERE id = 1")
        job = jobs_repo.update_job(self.conn, 1, "applied", "emailed recruiter")
        self.assertEqual(job["status"], "applied")
        self.assertIsNotNone(job["applied_at"])
        self.assertFalse(job["reposted"])
        self.assertEqual(job["notes"], "emailed recruiter")

    def test_update_unknown_job_returns_none(self):
        self.assertIsNone(jobs_repo.update_job(self.conn, 99, "saved", None))

    def test_bulk_update_and_counts(self):
        self.assertEqual(jobs_repo.bulk_update_status(self.conn, [1, 2], "ignored"), 2)
        counts = jobs_repo.status_counts(self.conn)
        self.assertEqual((counts["ignored"], counts["new"]), (2, 1))

    def test_ignore_company_only_touches_new_jobs_of_that_company(self):
        jobs_repo.update_job(self.conn, 1, "saved", None)
        self.conn.execute("UPDATE jobs SET company_key = 'stripe' WHERE id IN (1, 2)")
        self.assertEqual(jobs_repo.ignore_company_jobs(self.conn, "stripe"), 1)
        self.assertEqual(jobs_repo.get_job(self.conn, 1)["status"], "saved")


if __name__ == "__main__":
    unittest.main()
