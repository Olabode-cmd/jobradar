import unittest
from unittest import mock

from app.config import AppConfig
from app.domain.profile import ProfileIncompleteError, is_profile_ready
from app.pipeline import run_doctor, run_fetch, select_sources
from app.services import runs_service, sources_service


def config(**profile):
    return AppConfig(present=True, profile={"role": "", **profile})


class ProfileGateTests(unittest.TestCase):
    def test_blank_or_missing_role_is_not_ready(self):
        for profile in (None, {}, {"role": ""}, {"role": "   "}, {"role": None}):
            with self.subTest(profile=profile):
                self.assertFalse(is_profile_ready(profile))
        self.assertTrue(is_profile_ready({"role": "Nurse"}))

    def test_every_crawl_entry_point_refuses_before_touching_the_network(self):
        blank = config()
        with mock.patch("app.sources.fetcher.json_board.fetch") as network, \
             mock.patch.object(runs_service, "load_config", return_value=blank), \
             mock.patch.object(sources_service, "load_config", return_value=blank):
            for name, call in (
                ("select_sources", lambda: select_sources(blank, None)),
                ("run_fetch", lambda: run_fetch(blank)),
                ("run_doctor", lambda: run_doctor(blank)),
                ("dashboard run", lambda: runs_service.start_run(None, False)),
                ("source test", lambda: sources_service.test_source("remoteok")),
            ):
                with self.subTest(entry=name), self.assertRaises(ProfileIncompleteError):
                    call()
            network.assert_not_called()


class SourceSelectionTests(unittest.TestCase):
    def ids(self, **profile):
        return {source["id"] for source in select_sources(config(role="Nurse", **profile), None)}

    def test_country_driven_sources_are_skipped_without_target_countries(self):
        ids = self.ids(targetCountries=[])
        self.assertIn("remoteok", ids)
        self.assertFalse({"relocateme", "japandev"} & ids)

    def test_single_country_board_runs_only_for_its_country(self):
        self.assertNotIn("japandev", self.ids(targetCountries=["DE"]))
        self.assertIn("japandev", self.ids(targetCountries=["jp"]))
        self.assertIn("relocateme", self.ids(targetCountries=["DE"]))


if __name__ == "__main__":
    unittest.main()
