import unittest

from app.db.repositories import ingest
from app.pipeline.ingest import SeenIndex, process_batch
from tests.support import BOARD, NOW, TempDbTestCase, raw_job

PROFILE = {"role": "Engineer", "includeKeywords": ["react"], "remoteOnly": False, "maxAgeDays": None}


class RepostTests(TempDbTestCase):
    def setUp(self):
        super().setUp()
        process_batch(self.conn, [raw_job()], BOARD, PROFILE, SeenIndex(), NOW, dry_run=False)
        self.conn.execute("UPDATE jobs SET status = 'ignored', status_changed_at = ? WHERE id = 1", (NOW,))
        self.conn.commit()

    def status(self):
        return self.conn.execute("SELECT status, reposted FROM jobs WHERE id = 1").fetchone()

    def test_much_newer_posting_reopens_as_new(self):
        ingest.reopen_if_reposted(self.conn, 1, "2026-11-20T00:00:00+00:00", NOW)
        row = self.status()
        self.assertEqual((row["status"], row["reposted"]), ("new", 1))

    def test_recent_duplicate_stays_ignored(self):
        ingest.reopen_if_reposted(self.conn, 1, "2026-10-20T00:00:00+00:00", NOW)
        self.assertEqual(self.status()["status"], "ignored")

    def test_missing_status_changed_at_does_not_crash(self):
        self.conn.execute("UPDATE jobs SET status_changed_at = NULL WHERE id = 1")
        ingest.reopen_if_reposted(self.conn, 1, "2026-11-20T00:00:00+00:00", NOW)
        self.assertEqual(self.status()["status"], "new")


if __name__ == "__main__":
    unittest.main()
