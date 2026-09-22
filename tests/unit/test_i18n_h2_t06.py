"""Unit tests for Phase H2 Task H2-T06: i18n String Externalization."""

import json
import unittest
from pathlib import Path


class TestI18nExternalization(unittest.TestCase):
    def test_en_locale_file_exists_and_valid(self):
        locale_path = Path("ui/src/locales/en.json")
        self.assertTrue(locale_path.exists(), "ui/src/locales/en.json does not exist")

        with open(locale_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIn("common", data)
        self.assertIn("dashboard", data)
        self.assertIn("approval_queue", data)
        self.assertIn("audit_trail", data)
        self.assertIn("feature_review", data)
        self.assertIn("traceability", data)

        self.assertEqual(data["common"]["app_title"], "Antinode Norma BDD Platform")


if __name__ == "__main__":
    unittest.main()
