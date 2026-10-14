"""Tests for normalization helpers — no network, no DB."""

import unittest

from app.normalize import (
    canonicalize_url,
    company_key,
    dedupe_hash,
    fix_mojibake,
    html_to_text,
    normalize_title,
    to_iso,
)


class TestCompanyKey(unittest.TestCase):
    def test_strips_legal_suffixes(self):
        self.assertEqual(company_key("Stripe, Inc."), "stripe")
        self.assertEqual(company_key("Acme Corp"), "acme")
        self.assertEqual(company_key("Globex Ltd"), "globex")
        self.assertEqual(company_key("Reddit, Inc."), "reddit")

    def test_lowercases_and_collapses(self):
        self.assertEqual(company_key("  Acme   Corporation "), "acme")


class TestHtmlToText(unittest.TestCase):
    def test_blocks_become_lines_and_scripts_are_dropped(self):
        html = "<p>Build <b>things</b></p><script>alert(1)</script><ul><li>React</li><li>Node</li></ul>"
        self.assertEqual(html_to_text(html), "Build things\n\n- React\n- Node")

    def test_plain_text_passes_through(self):
        self.assertEqual(html_to_text("  Hello   world "), "Hello world")

    def test_empty_is_none(self):
        self.assertIsNone(html_to_text(""))
        self.assertIsNone(html_to_text(None))


class TestFixMojibake(unittest.TestCase):
    def test_repairs_double_encoded_text(self):
        broken = "We\u00e2\u0080\u0099re hiring \u00e2\u0080\u0094 apply".encode("utf-8").decode("utf-8")
        self.assertEqual(fix_mojibake(broken), "We\u2019re hiring \u2014 apply")

    def test_leaves_clean_and_unfixable_text_alone(self):
        self.assertEqual(fix_mojibake("Caf\u00e9 \u2014 ok"), "Caf\u00e9 \u2014 ok")
        mixed = "\u00e2\u0080\u0094 and \u2014"
        self.assertEqual(fix_mojibake(mixed), mixed)


class TestToIso(unittest.TestCase):
    def test_rfc2822(self):
        self.assertEqual(to_iso("Tue, 14 Oct 2026 08:00:00 +0000"), "2026-10-14T08:00:00+00:00")

    def test_offsets_are_converted_to_utc(self):
        self.assertEqual(to_iso("2026-09-09T10:50:29-04:00"), "2026-09-09T14:50:29+00:00")

    def test_epoch_seconds_and_milliseconds(self):
        self.assertEqual(to_iso(1760428800), "2025-10-14T08:00:00+00:00")
        self.assertEqual(to_iso(1760428800000), "2025-10-14T08:00:00+00:00")

    def test_garbage_is_none(self):
        self.assertIsNone(to_iso("sometime soon"))
        self.assertIsNone(to_iso(True))


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