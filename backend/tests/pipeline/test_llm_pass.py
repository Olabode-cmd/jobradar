import json
import unittest

from app.llm import LlmError, LlmReply
from app.pipeline.ingest import SeenIndex, process_batch
from app.pipeline.llm_pass import run_llm_pass
from tests.support import BOARD, NOW, TempDbTestCase, raw_job

PROFILE = {"role": "Engineer", "includeKeywords": ["react"], "remoteOnly": False, "maxAgeDays": None}


class ScriptedClient:
    """Replies per call from a list of replies or exceptions."""

    def __init__(self, *replies):
        self.replies = list(replies)
        self.calls = 0

    def complete(self, system, prompt, max_tokens=300):
        self.calls += 1
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return LlmReply(reply)


def verdict(fit=8, eligible="yes", reason="Good match."):
    return json.dumps({"fit": fit, "eligible": eligible, "reason": reason})


class LlmPassTests(TempDbTestCase):
    def setUp(self):
        super().setUp()
        process_batch(self.conn, [raw_job(1, "React Engineer"), raw_job(2, "Plumber", description="Pipes")],
                      BOARD, PROFILE, SeenIndex(), NOW, dry_run=False)

    def job(self, job_id):
        return self.conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()

    def test_stores_result_and_raises_score_with_a_reason(self):
        before = self.job(1)["score"]
        stats = run_llm_pass(self.conn, ScriptedClient(verdict(8), verdict(2)), PROFILE)
        row = self.job(1)
        self.assertEqual(stats["assessed"], 2)
        self.assertEqual(json.loads(row["llm_result"])["fit"], 8)
        self.assertEqual(row["score"], round(before + 4.0, 2))
        self.assertIn("AI fit 8/10: Good match.", json.loads(row["score_reasons"]))

    def test_no_verdict_restricts_with_a_visible_reason(self):
        run_llm_pass(self.conn, ScriptedClient(verdict(2, "no", "Needs US residency."), verdict()), PROFILE)
        restricted = [r for r in self.conn.execute("SELECT * FROM jobs") if r["eligibility"] == "restricted"]
        self.assertEqual(len(restricted), 1)
        self.assertIn("restricted (AI): Needs US residency.", json.loads(restricted[0]["score_reasons"]))

    def test_yes_upgrades_an_unclear_job(self):
        self.assertEqual(self.job(2)["eligibility"], "unclear")
        run_llm_pass(self.conn, ScriptedClient(verdict(), verdict(5, "yes")), PROFILE)
        self.assertEqual(self.job(2)["eligibility"], "eligible")

    def test_cached_results_are_not_assessed_again(self):
        run_llm_pass(self.conn, ScriptedClient(verdict(), verdict()), PROFILE)
        client = ScriptedClient()
        self.assertEqual(run_llm_pass(self.conn, client, PROFILE)["assessed"], 0)
        self.assertEqual(client.calls, 0)

    def test_the_per_run_cap_is_respected(self):
        client = ScriptedClient(verdict())
        self.assertEqual(run_llm_pass(self.conn, client, PROFILE, limit=1)["assessed"], 1)
        self.assertEqual(client.calls, 1)

    def test_fatal_error_stops_the_pass_and_reports_it(self):
        client = ScriptedClient(LlmError("auth", "Provider rejected the API key."), verdict())
        stats = run_llm_pass(self.conn, client, PROFILE)
        self.assertEqual((stats["assessed"], client.calls), (0, 1))
        self.assertEqual(stats["message"], "Provider rejected the API key.")

    def test_unparseable_answer_skips_that_job_and_continues(self):
        client = ScriptedClient("not json at all", verdict())
        stats = run_llm_pass(self.conn, client, PROFILE)
        self.assertEqual((stats["assessed"], stats["failed"], client.calls), (1, 1, 2))
        self.assertIsNone(stats["message"])

    def test_ignored_and_restricted_jobs_are_not_sent(self):
        self.conn.execute("UPDATE jobs SET status = 'ignored' WHERE id = 1")
        self.conn.execute("UPDATE jobs SET eligibility = 'restricted' WHERE id = 2")
        client = ScriptedClient()
        self.assertEqual(run_llm_pass(self.conn, client, PROFILE)["assessed"], 0)
        self.assertEqual(client.calls, 0)


if __name__ == "__main__":
    unittest.main()
