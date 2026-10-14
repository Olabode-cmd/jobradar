import unittest
from datetime import UTC, datetime, timedelta

from app.domain.eligibility import apply_rules, evaluate
from tests.support import normalized_job as job

PROFILE = {
    "role": "Software engineer",
    "includeKeywords": ["react", "typescript"],
    "rejectedPhrases": ["us only", "security clearance"],
    "remoteOnly": True,
    "blockedRegions": ["US"],
    "maxAgeDays": 14,
}


class ApplyRulesTests(unittest.TestCase):
    def test_eligible_when_keywords_match(self):
        self.assertEqual(apply_rules(job(), PROFILE), "eligible")

    def test_rejected_phrase_restricts(self):
        self.assertEqual(apply_rules(job(description="Must be US only."), PROFILE), "restricted")

    def test_blocked_region_phrase_restricts(self):
        self.assertEqual(apply_rules(job(description="You must be authorized to work in the US."), PROFILE), "restricted")

    def test_remote_only_rejects_onsite(self):
        self.assertEqual(apply_rules(job(remote_status=None, location_text="Lagos"), PROFILE), "restricted")

    def test_no_keyword_match_is_unclear(self):
        self.assertEqual(apply_rules(job(title="Plumber", description="Fix pipes."), PROFILE), "unclear")

    def test_no_include_keywords_means_eligible(self):
        self.assertEqual(apply_rules(job(title="Plumber"), dict(PROFILE, includeKeywords=[])), "eligible")

    def test_older_than_max_age_is_restricted(self):
        old = datetime.now(UTC) - timedelta(days=30)
        self.assertEqual(apply_rules(job(posted_at=old.isoformat()), PROFILE), "restricted")

    def test_blocked_company_restricts(self):
        profile = dict(PROFILE, blockedCompanies=["acme"])
        self.assertEqual(apply_rules(job(company_key="acme"), profile), "restricted")
        self.assertEqual(apply_rules(job(company_key="stripe"), profile), "eligible")

    def test_exclude_keyword_in_title_restricts(self):
        profile = dict(PROFILE, excludeKeywords=["senior"])
        self.assertEqual(apply_rules(job(title="Senior React Engineer"), profile), "restricted")
        self.assertEqual(apply_rules(job(title="React Engineer", description="We want a senior mindset"), profile), "eligible")

    def test_min_salary_restricts_only_when_listed_pay_is_lower(self):
        profile = dict(PROFILE, minSalary=100_000)
        self.assertEqual(apply_rules(job(salary_text="$60K - $80K"), profile), "restricted")
        self.assertEqual(apply_rules(job(salary_text="$90K - $140K"), profile), "eligible")
        self.assertEqual(apply_rules(job(salary_text=None), profile), "eligible")


class EvaluateTests(unittest.TestCase):
    def test_reason_explains_a_restriction(self):
        verdict, reason = evaluate(job(description="Must be US only."), PROFILE)
        self.assertEqual(verdict, "restricted")
        self.assertIn("us only", reason)

    def test_eligible_has_no_reason(self):
        self.assertEqual(evaluate(job(), PROFILE), ("eligible", None))


if __name__ == "__main__":
    unittest.main()
