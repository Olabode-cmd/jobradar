import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from app.config import ConfigFileError, default_config, load_config, mutate_config, paths, read_config_document, write_config_document


class ConfigDocumentTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = Path(tmp.name) / "jobradar.config.json"
        patcher = mock.patch.object(paths, "CONFIG_PATH", self.path)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_missing_file_returns_defaults(self):
        document, exists = read_config_document()
        self.assertFalse(exists)
        self.assertEqual(document, default_config())

    def test_partial_file_is_merged_over_defaults(self):
        self.path.write_text(json.dumps({"profile": {"role": "Writer"}}), encoding="utf-8")
        document, exists = read_config_document()
        self.assertTrue(exists)
        self.assertEqual((document["profile"]["role"], document["profile"]["maxAgeDays"]), ("Writer", 14))

    def test_invalid_json_and_non_objects_raise_a_conflict(self):
        for text in ["{not json", "[]"]:
            with self.subTest(text=text):
                self.path.write_text(text, encoding="utf-8")
                with self.assertRaises(ConfigFileError):
                    read_config_document()

    def test_write_roundtrip_leaves_no_temp_file(self):
        document = default_config()
        document["profile"]["role"] = "Analyst"
        write_config_document(document)
        self.assertEqual(json.loads(self.path.read_text(encoding="utf-8")), document)
        self.assertFalse(self.path.with_suffix(".json.tmp").exists())

    def test_mutate_keeps_unrelated_keys(self):
        self.path.write_text(json.dumps({"customSources": [{"name": "x"}], "extra": 1}), encoding="utf-8")
        mutate_config(lambda document: document["companies"].update(blocked=["acme"]))
        saved = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual((saved["customSources"], saved["extra"], saved["companies"]["blocked"]), ([{"name": "x"}], 1, ["acme"]))


class LoadConfigTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = Path(tmp.name) / "jobradar.config.json"
        for target, value in (("CONFIG_PATH", self.path), ("ENV_PATH", Path(tmp.name) / ".env")):
            patcher = mock.patch.object(paths, target, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_missing_file_is_reported_not_raised(self):
        config = load_config()
        self.assertFalse(config.present)
        self.assertIn("not found", config.errors[0])

    def test_type_errors_are_human_readable(self):
        self.path.write_text(json.dumps({"profile": {"maxAgeDays": "soon", "remoteOnly": "yes"}}), encoding="utf-8")
        errors = load_config().errors
        self.assertIn("jobradar.config.json: 'maxAgeDays' must be int or null", errors)
        self.assertIn("jobradar.config.json: 'remoteOnly' must be bool", errors)

    def test_contact_comes_from_preferences(self):
        self.path.write_text(json.dumps({"preferences": {"userAgentContact": "me@example.com"}}), encoding="utf-8")
        self.assertEqual(load_config().contact, "me@example.com")


if __name__ == "__main__":
    unittest.main()
