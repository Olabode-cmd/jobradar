import unittest

from app.llm import LlmError, LlmReply
from app.llm.assess import assess_job, build_prompt, parse_assessment

PROFILE = {"role": "Frontend engineer", "includeKeywords": ["react"], "remoteOnly": True, "blockedRegions": ["US"]}
JOB = {"title": "React Dev", "company": "Acme", "location_text": "Remote", "salary_text": None, "description": "Build UIs. " * 1000}


class ParseAssessmentTests(unittest.TestCase):
    def test_plain_json(self):
        result = parse_assessment('{"fit": 8, "eligible": "yes", "reason": "Matches React."}')
        self.assertEqual((result.fit, result.eligible, result.reason), (8, "yes", "Matches React."))

    def test_json_wrapped_in_prose_and_fences(self):
        result = parse_assessment('Sure!\n```json\n{"fit": 3.6, "eligible": "No", "reason": "US only"}\n```')
        self.assertEqual((result.fit, result.eligible), (4, "no"))

    def test_fit_is_clamped(self):
        self.assertEqual(parse_assessment('{"fit": 99, "eligible": "yes", "reason": ""}').fit, 10)
        self.assertEqual(parse_assessment('{"fit": -4, "eligible": "yes", "reason": ""}').fit, 0)

    def test_garbage_raises_an_unexpected_error(self):
        for text in ["", "I think it's good", '{"fit": "high", "eligible": "yes"}', '{"fit": 5, "eligible": "maybe"}']:
            with self.subTest(text=text), self.assertRaises(LlmError) as raised:
                parse_assessment(text)
            self.assertEqual(raised.exception.kind, "unexpected")


class PromptTests(unittest.TestCase):
    def test_includes_profile_and_posting_but_truncates_long_descriptions(self):
        prompt = build_prompt(PROFILE, JOB)
        self.assertIn("Frontend engineer", prompt)
        self.assertIn("Cannot work in (no right to work there): US", prompt)
        self.assertIn("React Dev", prompt)
        self.assertLess(len(prompt), 6000)


class AssessJobTests(unittest.TestCase):
    def test_uses_the_client_and_parses_its_reply(self):
        class Client:
            def complete(self, system, prompt, max_tokens=300):
                self.seen = (system, prompt, max_tokens)
                return LlmReply('{"fit": 7, "eligible": "unclear", "reason": "Region unclear."}')

        client = Client()
        result = assess_job(client, PROFILE, JOB)
        self.assertEqual((result.fit, result.eligible), (7, "unclear"))
        self.assertIn("React Dev", client.seen[1])


if __name__ == "__main__":
    unittest.main()
