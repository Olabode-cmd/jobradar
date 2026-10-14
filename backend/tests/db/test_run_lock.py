import json
import unittest
from datetime import UTC, datetime, timedelta

from app.db.repositories import run_lock
from tests.support import TempDbTestCase


class RunLockTests(TempDbTestCase):
    def test_second_acquire_is_refused_until_released(self):
        self.assertEqual(run_lock.acquire(self.conn, force=False), (True, None))
        acquired, message = run_lock.acquire(self.conn, force=False)
        self.assertFalse(acquired)
        self.assertIn("another run is active", message)
        run_lock.release(self.conn)
        self.assertTrue(run_lock.acquire(self.conn, force=False)[0])

    def test_force_overrides_an_active_lock(self):
        run_lock.acquire(self.conn, force=False)
        self.assertTrue(run_lock.acquire(self.conn, force=True)[0])

    def test_stale_lock_is_taken_over(self):
        old = (datetime.now(UTC) - timedelta(seconds=run_lock.STALE_AFTER_S + 5)).isoformat()
        self.conn.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?)",
            (run_lock.LOCK_KEY, json.dumps({"started_at": old, "heartbeat": old})),
        )
        self.assertTrue(run_lock.acquire(self.conn, force=False)[0])


if __name__ == "__main__":
    unittest.main()
