import unittest

from app.db.repositories import ingest, jobs
from app.db.repositories.jobs import JobFilters
from app.pipeline.ingest import SeenIndex, process_batch
from tests.support import BOARD, NOW, TempDbTestCase, raw_job

PROFILE = {"role": "Engineer", "includeKeywords": ["react"], "remoteOnly": False, "maxAgeDays": None}


class JobsRepoTests(TempDbTestCase):
    def setUp(self):
        super().setUp()
        process_batch(
            self.conn,
            [
                raw_job(1, "React Engineer"),
                raw_job(2, "Vue Engineer", company="Globex"),
                raw_job(3, "Plumber", company="Pipes Ltd", description="Pipes", remote=False),
            ],
            BOARD, PROFILE, SeenIndex(), NOW, dry_run=False,
        )

    def test_default_filter_hides_restricted_and_orders_by_score(self):
        self.conn.execute("UPDATE jobs SET eligibility = 'restricted' WHERE id = 3")
        items, total = jobs.list_jobs(self.conn, JobFilters())
        self.assertEqual(total, 2)
        self.assertEqual(items[0]["title"], "React Engineer")

    def test_search_matches_title_and_company_and_escapes_wildcards(self):
        self.assertEqual(jobs.list_jobs(self.conn, JobFilters(query="globex"))[1], 1)
        self.assertEqual(jobs.list_jobs(self.conn, JobFilters(query="%"))[1], 0)

    def test_remote_and_source_filters(self):
        self.assertEqual(jobs.list_jobs(self.conn, JobFilters(remote_only=True, eligibility=()))[1], 2)
        self.assertEqual(jobs.list_jobs(self.conn, JobFilters(source="nope", eligibility=()))[1], 0)

    def test_detail_has_text_description_and_source_links(self):
        job = jobs.get_job(self.conn, 1)
        self.assertEqual(job["description"], "React and TypeScript")
        self.assertEqual(job["source_links"][0]["source_id"], "board")
        self.assertTrue(job["score_reasons"])

    def test_source_listed_once_even_with_several_urls(self):
        ingest.attach_source(self.conn, 1, "board", "https://alt.example.com/1", NOW)
        items, _ = jobs.list_jobs(self.conn, JobFilters(query="React"))
        self.assertEqual(items[0]["sources"], ["board"])

    def test_status_update_sets_timestamps_and_clears_repost_flag(self):
        self.conn.execute("UPDATE jobs SET reposted = 1 WHERE id = 1")
        jobs.update_job(self.conn, 1, "applied", "emailed recruiter")
        job = jobs.get_job(self.conn, 1)
        self.assertEqual(job["status"], "applied")
        self.assertIsNotNone(job["applied_at"])
        self.assertFalse(job["reposted"])
        self.assertEqual(job["notes"], "emailed recruiter")

    def test_job_exists(self):
        self.assertTrue(jobs.job_exists(self.conn, 1))
        self.assertFalse(jobs.job_exists(self.conn, 99))

    def test_bulk_update_and_counts(self):
        self.assertEqual(jobs.bulk_update_status(self.conn, [1, 2], "ignored"), 2)
        counts = jobs.status_counts(self.conn)
        self.assertEqual((counts["ignored"], counts["new"]), (2, 1))

    def test_ignore_company_only_touches_new_jobs_of_that_company(self):
        jobs.update_job(self.conn, 1, "saved", None)
        self.conn.execute("UPDATE jobs SET company_key = 'stripe' WHERE id IN (1, 2)")
        self.assertEqual(jobs.ignore_company_jobs(self.conn, "stripe"), 1)
        self.assertEqual(jobs.get_job(self.conn, 1)["status"], "saved")


if __name__ == "__main__":
    unittest.main()
