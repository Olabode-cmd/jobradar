"""Tests for config read/write and the request schemas — no network, no DB."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from pydantic import ValidationError

from app import config
from app.schemas import ConfigUpdateIn

VALID_UPDATE = {
    "profile": {
        "role": "Designer",
        "includeKeywords": [" figma ", "Figma", "", "motion"],
        "excludeKeywords": [],
        "rejectedPhrases": ["us only"],
        "remoteOnly": True,
        "blockedRegions": ["US"],
        "timezonesOverlap": "  ",
        "minSalary": 40000,
        "maxAgeDays": 7,
    },
    "preferences": {"userAgentContact": "me@example.com"},
}


class SchemaTests(unittest.TestCase):
    def test_lists_are_trimmed_and_deduplicated(self):
        update = ConfigUpdateIn.model_validate(VALID_UPDATE)
        self.assertEqual(update.profile.includeKeywords, ["figma", "motion"])

    def test_blank_timezone_becomes_null(self):
        update = ConfigUpdateIn.model_validate(VALID_UPDATE)
        self.assertIsNone(update.profile.timezonesOverlap)

    def test_rejects_wrong_types(self):
        for field, bad in [("maxAgeDays", "14"), ("remoteOnly", "yes"), ("minSalary", -1), ("role", "")]:
            payload = json.loads(json.dumps(VALID_UPDATE))
            payload["profile"][field] = bad
            with self.subTest(field=field), self.assertRaises(ValidationError):
                ConfigUpdateIn.model_validate(payload)

    def test_rejects_unknown_profile_keys(self):
        payload = json.loads(json.dumps(VALID_UPDATE))
        payload["profile"]["surprise"] = 1
        with self.assertRaises(ValidationError):
            ConfigUpdateIn.model_validate(payload)


class ConfigFileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "jobradar.config.json"
        patcher = mock.patch.object(config, "CONFIG_PATH", self.path)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self.tmp.cleanup)

    def test_missing_file_returns_defaults(self):
        document, exists = config.read_config_document()
        self.assertFalse(exists)
        self.assertEqual(document, config.default_config())

    def test_partial_file_is_merged_over_defaults(self):
        self.path.write_text(json.dumps({"profile": {"role": "Writer"}}), encoding="utf-8")
        document, exists = config.read_config_document()
        self.assertTrue(exists)
        self.assertEqual(document["profile"]["role"], "Writer")
        self.assertEqual(document["profile"]["maxAgeDays"], 14)

    def test_invalid_json_raises(self):
        self.path.write_text("{not json", encoding="utf-8")
        with self.assertRaises(config.ConfigFileError):
            config.read_config_document()

    def test_non_object_raises(self):
        self.path.write_text("[]", encoding="utf-8")
        with self.assertRaises(config.ConfigFileError):
            config.read_config_document()

    def test_write_roundtrip_leaves_no_temp_file(self):
        document = config.default_config()
        document["profile"]["role"] = "Analyst"
        config.write_config_document(document)
        self.assertEqual(json.loads(self.path.read_text(encoding="utf-8")), document)
        self.assertFalse(self.path.with_suffix(".json.tmp").exists())


if __name__ == "__main__":
    unittest.main()
