import unittest

from app.domain.scoring import score_job
from tests.support import normalized_job as job

PROFILE = {"role": "Senior software engineer", "includeKeywords": ["react", "typescript"]}


class ScoreJobTests(unittest.TestCase):
    def test_keyword_in_title_scores_higher_than_in_description(self):
        title_match, _ = score_job(job(), PROFILE)
        body_only, _ = score_job(job(title="Software Engineer", description="We use React here."), PROFILE)
        self.assertGreater(title_match, body_only)

    def test_returns_reasons(self):
        score, reasons = score_job(job(), PROFILE)
        self.assertGreater(score, 0)
        self.assertTrue(any("react" in reason for reason in reasons))

    def test_seniority_match_beats_mismatch(self):
        matching, reasons = score_job(job(title="Senior Engineer"), PROFILE)
        mismatched, mismatch_reasons = score_job(job(title="Junior Engineer"), PROFILE)
        self.assertGreater(matching, mismatched)
        self.assertIn("seniority matches your role", reasons)
        self.assertIn("seniority differs from your role", mismatch_reasons)

    def test_company_board_link_adds_a_bonus(self):
        _, plain = score_job(job(apply_method="form"), PROFILE)
        _, own = score_job(job(apply_method="ats"), PROFILE)
        self.assertNotIn("applies on the company's own board", plain)
        self.assertIn("applies on the company's own board", own)

    def test_never_below_fallback(self):
        score, _ = score_job({"title": "x", "posted_at": "2000-01-01T00:00:00+00:00"}, {})
        self.assertEqual(score, 0.5)


if __name__ == "__main__":
    unittest.main()
