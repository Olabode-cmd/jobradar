import copy
import unittest

from pydantic import ValidationError

from app.api.schemas.config import ConfigUpdateIn
from app.api.schemas.settings import SettingsUpdateIn

VALID = {
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


class ConfigUpdateTests(unittest.TestCase):
    def test_lists_are_trimmed_and_deduplicated(self):
        self.assertEqual(ConfigUpdateIn.model_validate(VALID).profile.includeKeywords, ["figma", "motion"])

    def test_blank_timezone_becomes_null(self):
        self.assertIsNone(ConfigUpdateIn.model_validate(VALID).profile.timezonesOverlap)

    def test_rejects_wrong_types(self):
        for field, bad in [("maxAgeDays", "14"), ("remoteOnly", "yes"), ("minSalary", -1), ("role", "")]:
            payload = copy.deepcopy(VALID)
            payload["profile"][field] = bad
            with self.subTest(field=field), self.assertRaises(ValidationError):
                ConfigUpdateIn.model_validate(payload)

    def test_rejects_unknown_profile_keys(self):
        payload = copy.deepcopy(VALID)
        payload["profile"]["surprise"] = 1
        with self.assertRaises(ValidationError):
            ConfigUpdateIn.model_validate(payload)


class SettingsUpdateTests(unittest.TestCase):
    def test_omitted_fields_stay_none_so_they_are_left_unchanged(self):
        self.assertEqual(SettingsUpdateIn.model_validate({"api_key": "k"}).model_dump(),
                         {"api_key": "k", "provider": None, "model": None, "base_url": None})

    def test_provider_must_be_known(self):
        with self.assertRaises(ValidationError):
            SettingsUpdateIn.model_validate({"provider": "skynet"})


if __name__ == "__main__":
    unittest.main()
