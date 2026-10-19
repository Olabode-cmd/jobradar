import unittest

from app.core.errors import ConflictError
from app.db.repositories import jobs, run_lock, runs
from app.pipeline.ingest import SeenIndex, process_batch
from app.services import data_service
from tests.support import BOARD, NOW, TempDbTestCase, raw_job

PROFILE = {"role": "Engineer", "includeKeywords": ["react"], "remoteOnly": False, "maxAgeDays": None}


class ClearDataTests(TempDbTestCase):
    def setUp(self):
        super().setUp()
        process_batch(
            self.conn,
            [raw_job(1, "React Engineer"), raw_job(2, "React Developer"), raw_job(3, "React Designer")],
            BOARD, PROFILE, SeenIndex(), NOW, dry_run=False,
        )
        jobs.update_job(self.conn, 1, "saved", None)
        jobs.update_job(self.conn, 2, "ignored", None)
        run_id, _ = runs.create(self.conn, "cli")
        runs.record_sources(self.conn, run_id, {"board": {"fetched": 3, "new": 3, "duration_ms": 5}})

    def count(self, table):
        return self.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

    def test_clear_everything(self):
        self.assertEqual(data_service.clear_data(self.conn), {"deleted": 3, "kept": 0})
        self.assertEqual([self.count(t) for t in ("jobs", "job_sources", "runs", "run_sources")], [0, 0, 0, 0])

    def test_keep_triaged_leaves_saved_and_ignored_jobs_with_their_sources(self):
        self.assertEqual(data_service.clear_data(self.conn, keep_triaged=True), {"deleted": 1, "kept": 2})
        statuses = [row["status"] for row in self.conn.execute("SELECT status FROM jobs ORDER BY id")]
        self.assertEqual(statuses, ["saved", "ignored"])
        self.assertEqual(self.count("job_sources"), 2)
        self.assertEqual(self.count("runs"), 0)

    def test_cleared_job_ids_are_not_reused(self):
        data_service.clear_data(self.conn)
        process_batch(self.conn, [raw_job(9, "React Engineer")], BOARD, PROFILE, SeenIndex(), NOW, dry_run=False)
        self.assertEqual(self.conn.execute("SELECT id FROM jobs").fetchone()["id"], 4)

    def test_refuses_while_a_run_is_active_and_deletes_nothing(self):
        run_lock.acquire(self.conn, force=False)
        with self.assertRaises(ConflictError):
            data_service.clear_data(self.conn)
        self.assertEqual(self.count("jobs"), 3)

    def test_releases_the_run_lock_afterwards(self):
        data_service.clear_data(self.conn)
        self.assertTrue(run_lock.acquire(self.conn, force=False)[0])


if __name__ == "__main__":
    unittest.main()
