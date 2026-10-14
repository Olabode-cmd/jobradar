import unittest
from unittest import mock

from app.config import AppConfig
from app.core.errors import ConflictError
from app.db import open_db
from app.db.repositories import run_lock
from app.pipeline import PROGRESS, begin_run, execute_run, run_fetch
from app.sources import SourceResult
from tests.support import TempDbTestCase, raw_job

PROFILE = {"role": "Engineer", "includeKeywords": ["react"], "remoteOnly": False, "maxAgeDays": None}


def source(source_id):
    return {"id": source_id, "tier": "A", "kind": "board", "type": "api"}


class RunnerTests(TempDbTestCase):
    def config(self):
        return AppConfig(present=True, profile=PROFILE)

    def test_processing_error_in_one_source_does_not_stop_the_rest(self):
        results = {
            # a non-string URL makes normalization raise for the broken source's record
            "broken": SourceResult("broken", records=[raw_job(url=12345)]),
            "healthy": SourceResult("healthy", records=[raw_job(url="https://h.example.com/1", title="React Dev")]),
        }
        with mock.patch("app.pipeline.runner.resolve_enabled_sources", return_value=[source("broken"), source("healthy")]), \
                mock.patch("app.pipeline.runner.fetch_source", side_effect=lambda src, _ctx: results[src["id"]]):
            summary = run_fetch(self.config())

        self.assertEqual(summary["status"], "ok")
        self.assertIn("error", summary["per_source"]["broken"])
        self.assertEqual(summary["per_source"]["healthy"]["new"], 1)
        state = self.conn.execute("SELECT last_status FROM source_state WHERE source_id = 'broken'").fetchone()
        self.assertEqual(state["last_status"], "error")
        self.assertIsNotNone(self.conn.execute("SELECT finished_at FROM runs").fetchone()["finished_at"])

    def test_progress_tracks_each_source_and_the_lock_is_released(self):
        run_id, started = begin_run(self.conn, "dashboard")
        PROGRESS.start(run_id, started, ["a"], dry_run=False)
        with mock.patch("app.pipeline.runner.fetch_source", return_value=SourceResult("a", records=[raw_job()])):
            execute_run(self.conn, self.config(), run_id, started, [source("a")], False, progress=PROGRESS)
        snapshot = PROGRESS.snapshot()
        self.assertEqual(snapshot["state"], "finished")
        self.assertEqual((snapshot["sources"][0]["state"], snapshot["sources"][0]["new"]), ("ok", 1))
        self.assertTrue(run_lock.acquire(self.conn, force=False)[0])

    def test_company_health_from_ats_sources_is_recorded(self):
        result = SourceResult("lever", records=[], companies=[
            {"key": "lever:acme", "open_roles": 4, "error": None},
            {"key": "lever:gone", "open_roles": 0, "error": "board not found"},
        ])
        run_id, started = begin_run(self.conn, "cli")
        with mock.patch("app.pipeline.runner.fetch_source", return_value=result):
            execute_run(self.conn, self.config(), run_id, started, [source("lever")], False)
        rows = {r["company_key"]: r for r in self.conn.execute("SELECT * FROM company_state")}
        self.assertEqual(rows["lever:acme"]["open_roles"], 4)
        self.assertEqual(rows["lever:gone"]["last_error"], "board not found")

    def test_begin_run_refuses_while_another_is_active(self):
        begin_run(self.conn, "cli")
        with self.assertRaises(ConflictError):
            begin_run(self.conn, "dashboard")

    def test_cli_path_reports_blocked_instead_of_raising(self):
        begin_run(self.conn, "cli")
        summary = run_fetch(self.config())
        self.assertEqual(summary["status"], "blocked")


if __name__ == "__main__":
    unittest.main()
