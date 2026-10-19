import unittest

from app.pipeline.ingest import SeenIndex, process_batch
from tests.support import BOARD, NOW, TempDbTestCase, raw_job

PROFILE = {"role": "Software engineer", "includeKeywords": ["react"], "remoteOnly": False, "blockedRegions": [], "maxAgeDays": None}


class ProcessBatchTests(TempDbTestCase):
    def setUp(self):
        super().setUp()
        self.index = SeenIndex()

    def process(self, records, source=BOARD, dry_run=False):
        return process_batch(self.conn, records, source, PROFILE, self.index, NOW, dry_run)

    def test_in_batch_dedupe_by_url(self):
        stats = self.process([raw_job(), raw_job()])
        self.assertEqual((stats["fetched"], stats["new"], stats["known"]), (2, 1, 1))

    def test_eligible_job_is_stored_with_score(self):
        stats = self.process([raw_job()])
        row = self.conn.execute("SELECT eligibility, score FROM jobs").fetchone()
        self.assertEqual(row["eligibility"], "eligible")
        self.assertIsNotNone(row["score"])
        self.assertEqual((stats["new"], stats["dropped"]), (1, 0))

    def test_jobs_that_miss_the_profile_are_dropped_before_storage(self):
        stats = self.process([
            raw_job(1, title="Plumber", description="Pipes."),
            raw_job(2, title="Staff Designer", description="No overlap."),
            raw_job(3),
        ])
        self.assertEqual((stats["new"], stats["dropped"]), (1, 2))
        self.assertEqual(self.conn.execute("SELECT count(*) FROM jobs").fetchone()[0], 1)
        self.assertEqual(sum(stats["drop_reasons"].values()), 2)

    def test_excluded_title_keyword_is_dropped_and_reported(self):
        profile = dict(PROFILE, excludeKeywords=["senior"])
        stats = process_batch(self.conn, [raw_job()], BOARD, profile, self.index, NOW, False)
        self.assertEqual((stats["new"], stats["dropped"]), (0, 1))
        self.assertEqual(stats["drop_reasons"], {'title contains "senior"': 1})

    def test_dropped_jobs_are_counted_in_dry_runs_too(self):
        stats = self.process([raw_job(title="Plumber", description="Pipes.")], dry_run=True)
        self.assertEqual((stats["new"], stats["dropped"]), (0, 1))

    def test_cross_source_merge_by_hash(self):
        self.process([raw_job(url="https://a.example.com/job/1")])
        other = {"id": "otherboard", "tier": "A", "kind": "board", "type": "api"}
        stats = self.process([raw_job(url="https://b.example.com/job/1")], source=other)
        self.assertEqual((stats["new"], stats["known"]), (0, 1))
        links = self.conn.execute("SELECT source_id FROM job_sources WHERE job_id = 1 ORDER BY source_id").fetchall()
        self.assertEqual([row["source_id"] for row in links], ["board", "otherboard"])

    def test_dry_run_stores_nothing_but_counts_duplicates_once(self):
        stats = self.process([raw_job(), raw_job()], dry_run=True)
        self.assertEqual((stats["new"], stats["known"]), (1, 1))
        self.assertEqual(self.conn.execute("SELECT count(*) FROM jobs").fetchone()[0], 0)

    def test_records_without_title_or_link_are_skipped(self):
        stats = self.process([
            {"last_updated": 1, "legal": "terms"},
            raw_job(url=""),
            raw_job(title="", url="https://a.example.com/job/9"),
            raw_job(),
        ])
        self.assertEqual((stats["skipped"], stats["new"]), (3, 1))

    def test_email_list_is_stored_as_json_text(self):
        self.process([raw_job(emails=["jobs@stripe.com", "hr@stripe.com"])])
        self.assertEqual(self.conn.execute("SELECT emails FROM jobs").fetchone()["emails"], '["jobs@stripe.com", "hr@stripe.com"]')

    def test_known_urls_in_the_database_are_recognised_on_the_next_run(self):
        self.process([raw_job()])
        stats = process_batch(self.conn, [raw_job()], BOARD, PROFILE, SeenIndex.from_db(self.conn), NOW, False)
        self.assertEqual((stats["new"], stats["known"]), (0, 1))


if __name__ == "__main__":
    unittest.main()
