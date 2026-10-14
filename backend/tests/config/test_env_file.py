import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from app.config import env_file, paths
from app.core.errors import InvalidInputError


class EnvFileTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.env_path = Path(tmp.name) / ".env"
        self.example_path = Path(tmp.name) / ".env.example"
        for patcher in (
            mock.patch.object(paths, "ENV_PATH", self.env_path),
            mock.patch.object(paths, "ENV_EXAMPLE_PATH", self.example_path),
            mock.patch.dict(os.environ, {}, clear=False),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)
        for key in env_file.LLM_KEYS:
            os.environ.pop(key, None)

    def test_creates_from_example_when_missing_and_never_overwrites(self):
        self.example_path.write_text("API_KEY=\n# custom\n", encoding="utf-8")
        self.assertTrue(env_file.ensure_env_file())
        self.assertEqual(self.env_path.read_text(encoding="utf-8"), "API_KEY=\n# custom\n")
        self.env_path.write_text("API_KEY=mine\n", encoding="utf-8")
        self.assertFalse(env_file.ensure_env_file())
        self.assertEqual(self.env_path.read_text(encoding="utf-8"), "API_KEY=mine\n")

    def test_falls_back_to_builtin_template(self):
        env_file.ensure_env_file()
        self.assertIn("API_KEY=", self.env_path.read_text(encoding="utf-8"))

    def test_update_replaces_in_place_and_keeps_other_lines(self):
        self.env_path.write_text("# keep me\nAPI_KEY=\nOTHER=1\nLLM_MODEL=old\n", encoding="utf-8")
        env_file.update_env_values({"API_KEY": "sk-test-123", "LLM_MODEL": None, "LLM_BASE_URL": "http://localhost:11434/v1"})
        self.assertEqual(
            self.env_path.read_text(encoding="utf-8"),
            "# keep me\nAPI_KEY=sk-test-123\nOTHER=1\nLLM_MODEL=\nLLM_BASE_URL=http://localhost:11434/v1\n",
        )
        self.assertEqual(os.environ["API_KEY"], "sk-test-123")
        self.assertFalse(os.environ.get("LLM_MODEL"))

    def test_update_creates_file_when_missing(self):
        env_file.update_env_values({"API_KEY": "abc123"})
        self.assertEqual(env_file.read_env_values()["API_KEY"], "abc123")

    def test_unsafe_values_are_rejected_and_nothing_is_written(self):
        self.env_path.write_text("API_KEY=\n", encoding="utf-8")
        for bad in ["has space", "a\nb", "quote\"d", "x#y"]:
            with self.subTest(value=bad), self.assertRaises(InvalidInputError):
                env_file.update_env_values({"API_KEY": bad})
        self.assertEqual(self.env_path.read_text(encoding="utf-8"), "API_KEY=\n")

    def test_mask_never_reveals_the_middle(self):
        self.assertEqual(env_file.mask_secret("sk-ant-abcdefghijklmnop"), "sk-a…mnop")
        self.assertEqual(env_file.mask_secret("short"), "•••••")


if __name__ == "__main__":
    unittest.main()
