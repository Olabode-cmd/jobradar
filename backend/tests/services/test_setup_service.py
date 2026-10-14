import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from app.config import paths
from app.services.setup_service import run_setup


class SetupServiceTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        self.config = root / "jobradar.config.json"
        self.config_example = root / "jobradar.config.example.json"
        self.env = root / ".env"
        self.config_example.write_text('{"profile": {"role": "Example"}}', encoding="utf-8")
        db_path = str(root / "state" / "jobradar.db")
        for patcher in (
            mock.patch.object(paths, "CONFIG_PATH", self.config),
            mock.patch.object(paths, "CONFIG_EXAMPLE_PATH", self.config_example),
            mock.patch.object(paths, "ENV_PATH", self.env),
            mock.patch.object(paths, "ENV_EXAMPLE_PATH", root / "missing.example"),
            mock.patch.dict(os.environ, {"JOBRADAR_DB": db_path}),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)
        self.db_path = Path(db_path)

    def test_creates_env_config_and_database_on_a_fresh_clone(self):
        created = run_setup()
        self.assertEqual(len(created), 3)
        self.assertIn("API_KEY=", self.env.read_text(encoding="utf-8"))
        self.assertEqual(self.config.read_text(encoding="utf-8"), self.config_example.read_text(encoding="utf-8"))
        self.assertTrue(self.db_path.exists())

    def test_running_again_creates_nothing_and_overwrites_nothing(self):
        run_setup()
        self.env.write_text("API_KEY=mine\n", encoding="utf-8")
        self.config.write_text('{"profile": {"role": "Mine"}}', encoding="utf-8")
        self.assertEqual(run_setup(), [])
        self.assertEqual(self.env.read_text(encoding="utf-8"), "API_KEY=mine\n")
        self.assertIn("Mine", self.config.read_text(encoding="utf-8"))

    def test_works_without_an_example_config(self):
        self.config_example.unlink()
        created = run_setup()
        self.assertFalse(self.config.exists())
        self.assertEqual(len(created), 2)


if __name__ == "__main__":
    unittest.main()
