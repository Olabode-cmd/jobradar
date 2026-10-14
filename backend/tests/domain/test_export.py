import csv
import io
import unittest

from app.domain.export import COLUMNS, jobs_to_csv, jobs_to_markdown


def job(**overrides):
    base = {
        "id": 1, "title": "React Engineer", "company": "Acme", "location_text": "Remote", "remote": True,
        "status": "saved", "eligibility": "eligible", "score": 8.5, "posted_at": "2026-10-10T00:00:00+00:00",
        "apply_url": "https://jobs.example.com/1", "apply_method": "ats", "emails": ["jobs@acme.com", "hr@acme.com"],
        "salary_text": "$100K", "notes": "call back", "applied_at": None, "sources": ["remoteok", "remotive"],
    }
    base.update(overrides)
    return base


def parse(text):
    return list(csv.reader(io.StringIO(text)))


class CsvTests(unittest.TestCase):
    def test_header_and_row(self):
        rows = parse(jobs_to_csv([job()]))
        self.assertEqual(tuple(rows[0]), COLUMNS)
        row = dict(zip(COLUMNS, rows[1]))
        self.assertEqual((row["title"], row["remote"], row["emails"], row["sources"]),
                         ("React Engineer", "yes", "jobs@acme.com; hr@acme.com", "remoteok; remotive"))

    def test_quotes_and_commas_survive(self):
        rows = parse(jobs_to_csv([job(title='Dev, "senior" role', notes="line1\nline2")]))
        row = dict(zip(COLUMNS, rows[1]))
        self.assertEqual((row["title"], row["notes"]), ('Dev, "senior" role', "line1\nline2"))

    def test_formula_like_text_is_defused(self):
        rows = parse(jobs_to_csv([job(title='=HYPERLINK("http://evil","x")', company="+cmd", notes="@SUM(A1)")]))
        row = dict(zip(COLUMNS, rows[1]))
        for column in ("title", "company", "notes"):
            self.assertTrue(row[column].startswith("'"), column)

    def test_empty_export_is_just_the_header(self):
        self.assertEqual(len(parse(jobs_to_csv([]))), 1)


class MarkdownTests(unittest.TestCase):
    def test_groups_by_status_with_links_notes_and_contacts(self):
        text = jobs_to_markdown([job(), job(id=2, title="Plumber", status="applied", apply_url=None, notes=None, emails=[])])
        self.assertIn("## Saved (1)", text)
        self.assertIn("## Applied (1)", text)
        self.assertIn("- [React Engineer](https://jobs.example.com/1) — Acme · Remote · score 8.5", text)
        self.assertIn("  - Notes: call back", text)
        self.assertIn("  - Contact: jobs@acme.com, hr@acme.com", text)
        self.assertIn("- Plumber — Acme", text)

    def test_brackets_in_titles_cannot_break_the_link(self):
        self.assertIn("[Dev \\[remote\\]](https://jobs.example.com/1)", jobs_to_markdown([job(title="Dev [remote]")]))


if __name__ == "__main__":
    unittest.main()
