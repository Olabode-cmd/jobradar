import unittest

from app.domain.keys import company_key, dedupe_hash, normalize_title
from app.domain.urls import canonicalize_url


class CompanyKeyTests(unittest.TestCase):
    def test_strips_legal_suffixes(self):
        self.assertEqual(company_key("Stripe, Inc."), "stripe")
        self.assertEqual(company_key("Acme Corp"), "acme")
        self.assertEqual(company_key("Globex Ltd"), "globex")

    def test_lowercases_and_collapses(self):
        self.assertEqual(company_key("  Acme   Corporation "), "acme")


class NormalizeTitleTests(unittest.TestCase):
    def test_strips_qualifiers(self):
        self.assertEqual(normalize_title("Senior Engineer (Remote)"), "senior engineer")
        self.assertEqual(normalize_title("Engineer [Remote]"), "engineer")

    def test_collapses_whitespace(self):
        self.assertEqual(normalize_title("  Senior   Engineer  "), "senior engineer")


class DedupeHashTests(unittest.TestCase):
    def test_ignores_company_suffix_variants(self):
        self.assertEqual(dedupe_hash("Stripe, Inc.", "Senior Engineer (Remote)"), dedupe_hash("Stripe", "Senior Engineer"))

    def test_none_for_empty(self):
        self.assertIsNone(dedupe_hash("", ""))


class CanonicalizeUrlTests(unittest.TestCase):
    def test_strips_tracking_params_and_fragment(self):
        self.assertEqual(
            canonicalize_url("https://jobs.example.com/1?utm_source=news&id=5&fbclid=abc#apply"),
            "https://jobs.example.com/1?id=5",
        )

    def test_keeps_clean_url_and_lowercases_host(self):
        self.assertEqual(canonicalize_url("https://Jobs.Example.com/A/"), "https://jobs.example.com/A/")


if __name__ == "__main__":
    unittest.main()
