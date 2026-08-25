from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from app.config import AppConfig


class AppConfigTest(unittest.TestCase):
    def test_save_load_roundtrip_preserves_appearance(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch("app.config.get_config_dir", return_value=Path(tmp)):
                cfg = AppConfig(language="en", appearance="light", path_overrides={"zed": "/data/zed"})
                cfg.save()
                loaded = AppConfig.load()
        self.assertEqual(loaded.language, "en")
        self.assertEqual(loaded.appearance, "light")
        self.assertEqual(loaded.path_overrides, {"zed": "/data/zed"})

    def test_missing_config_defaults_to_dark_appearance(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch("app.config.get_config_dir", return_value=Path(tmp)):
                loaded = AppConfig.load()
        self.assertEqual(loaded.appearance, "dark")


if __name__ == "__main__":
    unittest.main()
