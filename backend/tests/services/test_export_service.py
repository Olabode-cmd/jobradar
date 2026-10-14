import unittest

from app.core.errors import InvalidInputError
from app.db.repositories import jobs
from app.pipeline.ingest import SeenIndex, process_batch
from app.services import export_service
from tests.support import BOARD, NOW, TempDbTestCase, raw_job

PROFILE = {"role": "Engineer", "includeKeywords": ["react"], "remoteOnly": False, "maxAgeDays": None}


class ExportServiceTests(TempDbTestCase):
    def setUp(self):
        super().setUp()
        process_batch(self.conn, [raw_job(1, "React Engineer"), raw_job(2, "Vue Engineer", company="Globex")],
                      BOARD, PROFILE, SeenIndex(), NOW, dry_run=False)
        jobs.update_job(self.conn, 2, "applied", "sent CV")

    def test_exports_every_job_by_default(self):
        body, media_type, filename = export_service.export_jobs(self.conn, "csv", ())
        self.assertEqual(body.count("\n"), 3)
        self.assertTrue(media_type.startswith("text/csv"))
        self.assertTrue(filename.startswith("jobradar-") and filename.endswith(".csv"))

    def test_status_filter(self):
        body, _, _ = export_service.export_jobs(self.conn, "markdown", ("applied",))
        self.assertIn("Vue Engineer", body)
        self.assertNotIn("React Engineer", body)
        self.assertIn("Notes: sent CV", body)

    def test_rejects_unknown_format_and_status(self):
        with self.assertRaises(InvalidInputError):
            export_service.export_jobs(self.conn, "xlsx", ())
        with self.assertRaises(InvalidInputError):
            export_service.export_jobs(self.conn, "csv", ("bogus",))


if __name__ == "__main__":
    unittest.main()
