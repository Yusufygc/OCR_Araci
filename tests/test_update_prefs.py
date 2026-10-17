import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.utils.updater import update_prefs
from src.utils.updater.update_prefs import UpdatePreferences


class TestUpdatePrefs(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = Path(self._tmp.name) / "alt" / "updates.json"

    def test_defaults_when_missing_or_corrupt(self):
        self.assertEqual(update_prefs.load_preferences(self.path), UpdatePreferences())
        self.path.parent.mkdir(parents=True)
        self.path.write_text("{bozuk", encoding="utf-8")
        self.assertEqual(update_prefs.load_preferences(self.path), UpdatePreferences())
        self.path.write_text("[1]", encoding="utf-8")
        self.assertEqual(update_prefs.load_preferences(self.path), UpdatePreferences())

    def test_save_and_load_roundtrip(self):
        prefs = UpdatePreferences(check_on_startup=False, skipped_version="1.2.0")
        self.assertTrue(update_prefs.save_preferences(prefs, self.path))
        self.assertEqual(update_prefs.load_preferences(self.path), prefs)

    def test_disabled_by_env_or_empty_repo(self):
        with patch.object(update_prefs, "RELEASE_REPO", "sahip/depo"):
            self.assertFalse(update_prefs.is_update_check_disabled({}))
            self.assertTrue(update_prefs.is_update_check_disabled({"KUSURSUZOCR_NO_UPDATE_CHECK": "1"}))
        with patch.object(update_prefs, "RELEASE_REPO", ""):
            self.assertTrue(update_prefs.is_update_check_disabled({}))

    def test_startup_check_only_when_frozen_and_enabled(self):
        prefs = UpdatePreferences(check_on_startup=True)
        with patch.object(update_prefs, "RELEASE_REPO", "sahip/depo"), patch.dict("os.environ", {}, clear=False):
            with patch.dict("os.environ", {"KUSURSUZOCR_NO_UPDATE_CHECK": ""}):
                self.assertTrue(update_prefs.should_check_on_startup(prefs, frozen=True))
                self.assertFalse(update_prefs.should_check_on_startup(prefs, frozen=False))
                self.assertFalse(update_prefs.should_check_on_startup(UpdatePreferences(check_on_startup=False), frozen=True))


if __name__ == "__main__":
    unittest.main()
