import os
import tempfile
import unittest
from pathlib import Path

from config.settings_loader import SettingsLoader


class SettingsLoaderTestCase(unittest.TestCase):
    def test_env_api_key_takes_precedence_over_settings_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            settings_path = tmp_path / "settings.json"
            dotenv_path = tmp_path / ".env"

            settings_path.write_text('{"GeminiApiKey": "from-settings"}', encoding="utf-8")
            dotenv_path.write_text("GEMINI_API_KEY=from-env\n", encoding="utf-8")

            loader = SettingsLoader(path=str(settings_path))

            self.assertEqual(loader.get_gemini_api_key(), "from-env")

    def test_settings_json_is_used_when_env_is_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            settings_path = tmp_path / "settings.json"
            settings_path.write_text('{"GeminiApiKey": "from-settings"}', encoding="utf-8")

            loader = SettingsLoader(path=str(settings_path))

            self.assertEqual(loader.get_gemini_api_key(), "from-settings")


if __name__ == "__main__":
    unittest.main()
