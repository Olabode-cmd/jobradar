"""Pipeline tests: in-batch dedupe, cross-source merge, repost rule, store-then-filter.

Uses a temp SQLite file via JOBRADAR_DB — no network.
"""

import os
import tempfile
import unittest
from unittest import mock

from app.config import AppConfig
from app.db import open_db
from app.pipeline import _maybe_repost, acquire_run_lock, create_run, execute_run, process_batch, run_fetch
from app.run_progress import PROGRESS
from app.sources.drivers import SourceResult

PROFILE = {
    "role": "Software engineer",
    "includeKeywords": ["react"],
    "rejectedPhrases": [],
    "remoteOnly": False,
    "blockedRegions": [],
    "maxAgeDays": 14,
}

SOURCE = {"id": "testboard", "tier": "A", "kind": "board", "type": "api"}


def raw(title="Senior React Engineer", company="Stripe", url="https://a.example.com/job/1", **overrides):
    record = {
        "title": title,
        "company": company,
        "url": url,
        "location": "Remote",
        "description": "React everywhere.",
        "date": "2026-10-01T00:00:00+00:00",
        "remote": True,
    }
    record.update(overrides)
    return record


class PipelineTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        os.environ["JOBRADAR_DB"] = self.tmp.name
        self.conn = open_db()
        self.now = "2026-10-14T00:00:00+00:00"
        self.seen_urls: set[str] = set()
        self.seen_hashes: set[str] = set()
        self.url_to_id: dict[str, int] = {}
        self.hash_to_id: dict[str, int] = {}

    def tearDown(self):
        self.conn.close()
        os.unlink(self.tmp.name)
        os.environ.pop("JOBRADAR_DB", None)

    def _process(self, records, source=SOURCE):
        return process_batch(
            self.conn, records, source, PROFILE,
            self.seen_urls, self.seen_hashes, self.url_to_id, self.hash_to_id,
            self.now, dry_run=False,
        )

    def test_in_batch_dedupe_by_url(self):
        stats = self._process([raw(), raw(url="https://a.example.com/job/1")])
        self.assertEqual(stats["fetched"], 2)
        self.assertEqual(stats["new"], 1)
        self.assertEqual(stats["known"], 1)

    def test_store_then_filter_records_eligibility(self):
        stats = self._process([raw(title="Plumber", description="Pipes.")])
        self.assertEqual(stats["new"], 1)
        row = self.conn.execute("SELECT eligibility, score FROM jobs").fetchone()
        self.assertEqual(row["eligibility"], "unclear")
        self.assertIsNotNone(row["score"])

    def test_cross_source_merge_by_hash(self):
        self._process([raw(url="https://a.example.com/job/1")])
        other = {"id": "otherboard", "tier": "A", "kind": "board", "type": "api"}
        stats = self._process([raw(url="https://b.example.com/job/1")], source=other)
        self.assertEqual(stats["new"], 0)
        self.assertEqual(stats["known"], 1)
        links = self.conn.execute(
            "SELECT source_id FROM job_sources WHERE job_id = 1 ORDER BY source_id"
        ).fetchall()
        self.assertEqual([r["source_id"] for r in links], ["otherboard", "testboard"])

    def test_repost_rule_reopens_ignored_job(self):
        self._process([raw()])
        self.conn.execute("UPDATE jobs SET status = 'ignored', status_changed_at = ? WHERE id = 1", (self.now,))
        self.conn.commit()
        newer = "2026-11-20T00:00:00+00:00"
        _maybe_repost(self.conn, 1, newer, self.now)
        row = self.conn.execute("SELECT status, reposted FROM jobs WHERE id = 1").fetchone()
        self.assertEqual(row["status"], "new")
        self.assertEqual(row["reposted"], 1)

    def test_recent_repost_stays_ignored(self):
        self._process([raw()])
        self.conn.execute("UPDATE jobs SET status = 'ignored', status_changed_at = ? WHERE id = 1", (self.now,))
        self.conn.commit()
        recent = "2026-10-20T00:00:00+00:00"  # 6 days after the change
        _maybe_repost(self.conn, 1, recent, self.now)
        row = self.conn.execute("SELECT status FROM jobs WHERE id = 1").fetchone()
        self.assertEqual(row["status"], "ignored")

    def test_dry_run_does_not_store(self):
        stats = process_batch(
            self.conn, [raw()], SOURCE, PROFILE,
            self.seen_urls, self.seen_hashes, self.url_to_id, self.hash_to_id,
            self.now, dry_run=True,
        )
        self.assertEqual(stats["new"], 1)
        count = self.conn.execute("SELECT count(*) FROM jobs").fetchone()[0]
        self.assertEqual(count, 0)

    def test_records_without_title_or_link_are_skipped(self):
        stats = self._process([
            {"last_updated": 1, "legal": "terms"},
            raw(url=""),
            raw(title="", url="https://a.example.com/job/9"),
            raw(),
        ])
        self.assertEqual(stats["skipped"], 3)
        self.assertEqual(stats["new"], 1)

    def test_dry_run_counts_in_batch_duplicates_once(self):
        stats = process_batch(
            self.conn, [raw(), raw()], SOURCE, PROFILE,
            self.seen_urls, self.seen_hashes, self.url_to_id, self.hash_to_id,
            self.now, dry_run=True,
        )
        self.assertEqual((stats["new"], stats["known"]), (1, 1))

    def test_email_list_is_stored_as_json_text(self):
        stats = self._process([raw(emails=["jobs@stripe.com", "hr@stripe.com"])])
        self.assertEqual(stats["new"], 1)
        row = self.conn.execute("SELECT emails FROM jobs").fetchone()
        self.assertEqual(row["emails"], '["jobs@stripe.com", "hr@stripe.com"]')


class RunFetchIsolationTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        os.environ["JOBRADAR_DB"] = self.tmp.name

    def tearDown(self):
        os.unlink(self.tmp.name)
        os.environ.pop("JOBRADAR_DB", None)

    def test_progress_tracks_each_source_and_lock_is_released(self):
        sources = [{"id": "a", "tier": "A", "kind": "board", "type": "api"}]
        conn = open_db()
        try:
            acquire_run_lock(conn, force=False)
            run_id, started = create_run(conn, "dashboard")
            PROGRESS.start(run_id, started, ["a"], dry_run=False)
            with mock.patch("app.pipeline.fetch_source", return_value=SourceResult("a", records=[raw()])):
                execute_run(conn, AppConfig(present=True, profile=PROFILE), run_id, started, sources, False, update_progress=True)
            snapshot = PROGRESS.snapshot()
            ok_again, _ = acquire_run_lock(conn, force=False)
        finally:
            conn.close()
        self.assertEqual(snapshot["state"], "finished")
        self.assertEqual((snapshot["sources"][0]["state"], snapshot["sources"][0]["new"]), ("ok", 1))
        self.assertTrue(ok_again)

    def test_processing_error_in_one_source_does_not_stop_the_rest(self):
        sources = [
            {"id": "broken", "tier": "A", "kind": "board", "type": "api"},
            {"id": "healthy", "tier": "A", "kind": "board", "type": "api"},
        ]
        # A non-string URL makes normalization raise for the broken source's record.
        results = {
            "broken": SourceResult("broken", records=[raw(url=12345)]),
            "healthy": SourceResult("healthy", records=[raw(url="https://h.example.com/1", title="React Dev")]),
        }
        config = AppConfig(present=True, profile=PROFILE)

        with mock.patch("app.pipeline.resolve_enabled_sources", return_value=sources), mock.patch(
            "app.pipeline.fetch_source", side_effect=lambda source, _config: results[source["id"]]
        ):
            summary = run_fetch(config)

        self.assertEqual(summary["status"], "ok")
        self.assertIn("error", summary["per_source"]["broken"])
        self.assertEqual(summary["per_source"]["healthy"]["new"], 1)
        conn = open_db()
        try:
            state = conn.execute("SELECT last_status FROM source_state WHERE source_id = 'broken'").fetchone()
            finished = conn.execute("SELECT finished_at FROM runs").fetchone()
        finally:
            conn.close()
        self.assertEqual(state["last_status"], "error")
        self.assertIsNotNone(finished["finished_at"])


if __name__ == "__main__":
    unittest.main()