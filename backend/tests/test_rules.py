"""Tests for the eligibility rules and scoring — no network, no DB."""

import unittest
from datetime import datetime, timedelta, timezone

from app.rules import apply_rules, score_job

PROFILE = {
    "role": "Software engineer",
    "includeKeywords": ["react", "typescript"],
    "rejectedPhrases": ["us only", "security clearance"],
    "remoteOnly": True,
    "blockedRegions": ["US"],
    "maxAgeDays": 14,
}


def job(**overrides):
    base = {
        "title": "Senior React Engineer",
        "description": "Build products with React and TypeScript.",
        "location_text": "Remote",
        "remote_status": "remote",
        "posted_at": datetime.now(timezone.utc).isoformat(),
        "apply_url": "https://jobs.example.com/1",
    }
    base.update(overrides)
    return base


class TestApplyRules(unittest.TestCase):
    def test_eligible_when_keywords_match(self):
        self.assertEqual(apply_rules(job(), PROFILE), "eligible")

    def test_rejected_phrase_restricts(self):
        self.assertEqual(apply_rules(job(description="Must be US only."), PROFILE), "restricted")

    def test_blocked_region_phrase_restricts(self):
        self.assertEqual(
            apply_rules(job(description="You must be authorized to work in the US."), PROFILE),
            "restricted",
        )

    def test_remote_only_rejects_onsite(self):
        self.assertEqual(apply_rules(job(remote_status=None, location_text="Lagos"), PROFILE), "restricted")

    def test_no_keyword_match_is_unclear(self):
        self.assertEqual(
            apply_rules(job(title="Plumber", description="Fix pipes."), PROFILE),
            "unclear",
        )

    def test_blocked_company_restricts(self):
        profile = dict(PROFILE, blockedCompanies=["acme"])
        self.assertEqual(apply_rules(job(company_key="acme"), profile), "restricted")
        self.assertEqual(apply_rules(job(company_key="stripe"), profile), "eligible")

    def test_no_include_keywords_means_eligible(self):
        empty = dict(PROFILE, includeKeywords=[])
        self.assertEqual(apply_rules(job(title="Plumber"), empty), "eligible")

    def test_older_than_max_age_is_restricted(self):
        old = datetime.now(timezone.utc) - timedelta(days=30)
        self.assertEqual(apply_rules(job(posted_at=old.isoformat()), PROFILE), "restricted")


class TestScoreJob(unittest.TestCase):
    def test_keyword_in_title_scores_higher(self):
        title_match, _ = score_job(job(), PROFILE)
        desc_only, _ = score_job(job(title="Software Engineer", description="We use React here."), PROFILE)
        self.assertGreater(title_match, desc_only)

    def test_returns_reasons(self):
        score, reasons = score_job(job(), PROFILE)
        self.assertGreater(score, 0)
        self.assertTrue(any("react" in r for r in reasons))


if __name__ == "__main__":
    unittest.main()