"""Tests for normalization helpers — no network, no DB."""

import unittest

from app.normalize import canonicalize_url, company_key, dedupe_hash, normalize_title


class TestCompanyKey(unittest.TestCase):
    def test_strips_legal_suffixes(self):
        self.assertEqual(company_key("Stripe, Inc."), "stripe")
        self.assertEqual(company_key("Acme Corp"), "acme")
        self.assertEqual(company_key("Globex Ltd"), "globex")
        self.assertEqual(company_key("Reddit, Inc."), "reddit")

    def test_lowercases_and_collapses(self):
        self.assertEqual(company_key("  Acme   Corporation "), "acme")


class TestNormalizeTitle(unittest.TestCase):
    def test_strips_qualifiers(self):
        self.assertEqual(normalize_title("Senior Engineer (Remote)"), "senior engineer")
        self.assertEqual(normalize_title("Engineer [Remote]"), "engineer")

    def test_collapses_whitespace(self):
        self.assertEqual(normalize_title("  Senior   Engineer  "), "senior engineer")


class TestDedupeHash(unittest.TestCase):
    def test_ignores_company_suffix_variants(self):
        self.assertEqual(
            dedupe_hash("Stripe, Inc.", "Senior Engineer (Remote)"),
            dedupe_hash("Stripe", "Senior Engineer"),
        )

    def test_none_for_empty(self):
        self.assertIsNone(dedupe_hash("", ""))


class TestCanonicalizeUrl(unittest.TestCase):
    def test_strips_tracking_params(self):
        self.assertEqual(
            canonicalize_url("https://jobs.example.com/1?utm_source=news&id=5&fbclid=abc#apply"),
            "https://jobs.example.com/1?id=5",
        )

    def test_keeps_clean_url(self):
        self.assertEqual(
            canonicalize_url("https://Jobs.Example.com/A/"),
            "https://jobs.example.com/A/",
        )


if __name__ == "__main__":
    unittest.main()