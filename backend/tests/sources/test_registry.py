import unittest

from app.config import AppConfig
from app.sources import list_all_sources, resolve_enabled_sources


def ids(sources):
    return {source["id"] for source in sources}


class RegistryTests(unittest.TestCase):
    def test_defaults_include_boards_and_every_ats_provider(self):
        enabled = ids(resolve_enabled_sources(AppConfig(present=True)))
        self.assertTrue({"remoteok", "hackernews", "greenhouse", "lever", "breezy"} <= enabled)

    def test_disabled_wins(self):
        config = AppConfig(present=True, sources={"disabled": ["remoteok"], "enabled": ["remoteok"]})
        self.assertNotIn("remoteok", ids(resolve_enabled_sources(config)))

    def test_opt_in_enables_a_source_that_ships_off(self):
        # Simulates a Tier C preset: defaultEnabled false, switched on by the user.
        from app.sources import registry

        original = registry.load_presets
        registry.load_presets = lambda: [{"id": "glassdoor", "tier": "C", "type": "selector", "defaultEnabled": False}]
        try:
            self.assertNotIn("glassdoor", ids(resolve_enabled_sources(AppConfig(present=True))))
            self.assertIn("glassdoor", ids(resolve_enabled_sources(AppConfig(present=True, sources={"enabled": ["glassdoor"]}))))
        finally:
            registry.load_presets = original

    def test_custom_sources_are_namespaced_and_marked(self):
        config = AppConfig(present=True, custom_sources=[{"name": "jobberman", "startUrl": "https://x", "itemSelector": "li"}])
        custom = next(s for s in list_all_sources(config) if s["id"] == "custom:jobberman")
        self.assertTrue(custom["custom"] and custom["enabled"])


if __name__ == "__main__":
    unittest.main()
