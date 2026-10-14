import unittest

from app.domain.dates import parse_datetime, to_iso


class ToIsoTests(unittest.TestCase):
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
        self.assertIsNone(to_iso(""))


class ParseDatetimeTests(unittest.TestCase):
    def test_naive_dates_become_utc(self):
        self.assertEqual(parse_datetime("2026-10-14T00:00:00").utcoffset().total_seconds(), 0)

    def test_z_suffix(self):
        self.assertIsNotNone(parse_datetime("2026-10-14T00:00:00Z"))


if __name__ == "__main__":
    unittest.main()
