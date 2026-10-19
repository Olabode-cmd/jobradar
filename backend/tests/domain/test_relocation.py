import unittest

from app.domain.eligibility import evaluate
from app.domain.relocation import job_offers_relocation, offers_relocation
from app.domain.scoring import score_job
from tests.support import normalized_job as job

PROFILE = {"role": "Engineer", "includeKeywords": [], "remoteOnly": True, "openToRelocation": True}


class OffersRelocationTests(unittest.TestCase):
    def test_offers_in_several_languages(self):
        for text in (
            "We offer full visa and relocation support for international candidates.",
            "International relocation support is provided if required.",
            "Wir übernehmen die Umzugskosten.",
            "Verhuiskosten worden vergoed.",
            "引越し支援あり",
        ):
            with self.subTest(text=text):
                self.assertTrue(offers_relocation(text))

    def test_negated_offers_do_not_count(self):
        for text in (
            "We cannot sponsor visas or support relocation at this time.",
            "Relocation support is not available for this role.",
            "No relocation assistance.",
            "Leider keine Umzugskosten.",
        ):
            with self.subTest(text=text):
                self.assertFalse(offers_relocation(text))

    def test_demands_on_the_candidate_are_not_offers(self):
        self.assertFalse(offers_relocation("Candidates must be willing to relocate to Munich."))

    def test_a_later_clause_can_still_offer(self):
        self.assertTrue(offers_relocation("No remote work, but we provide a relocation package."))

    def test_source_flag_vouches_for_the_job(self):
        self.assertTrue(job_offers_relocation({"offers_relocation": True, "description": ""}))


class RelocationEligibilityTests(unittest.TestCase):
    def test_onsite_with_relocation_is_eligible_even_when_remote_only(self):
        onsite = job(remote_status=None, description="Relocation package included.")
        self.assertEqual(evaluate(onsite, PROFILE), ("eligible", None))

    def test_onsite_without_relocation_is_restricted(self):
        verdict, reason = evaluate(job(remote_status=None, description="Office in Berlin."), PROFILE)
        self.assertEqual((verdict, reason), ("restricted", "on-site without relocation support"))

    def test_remote_jobs_are_unaffected(self):
        self.assertEqual(evaluate(job(), PROFILE)[0], "eligible")

    def test_flag_off_keeps_the_old_remote_only_rule(self):
        profile = dict(PROFILE, openToRelocation=False)
        self.assertEqual(evaluate(job(remote_status=None, description="Relocation package."), profile)[1], "not remote")

    def test_relocation_raises_the_score(self):
        onsite = job(remote_status=None, description="Relocation package included.")
        plain = job(remote_status=None, description="Office in Berlin.")
        self.assertGreater(score_job(onsite, PROFILE)[0], score_job(plain, PROFILE)[0])


if __name__ == "__main__":
    unittest.main()
