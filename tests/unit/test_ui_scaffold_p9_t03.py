"""Unit tests for Phase 9 Task P9-T03: Frontend Scaffold Integrity."""

import json
import unittest
from pathlib import Path


class TestUIScaffoldIntegrity(unittest.TestCase):
    def setUp(self):
        self.ui_dir = Path("ui")

    def test_ui_directory_and_package_json(self):
        self.assertTrue(self.ui_dir.exists() and self.ui_dir.is_dir())
        pkg_json = self.ui_dir / "package.json"
        self.assertTrue(pkg_json.exists())

        data = json.loads(pkg_json.read_text(encoding="utf-8"))
        self.assertEqual(data["name"], "norma-ui")
        self.assertIn("react", data["dependencies"])
        self.assertIn("vite", data["devDependencies"])
        self.assertIn("tailwindcss", data["devDependencies"])

    def test_vite_and_tsconfig_configs(self):
        vite_cfg = self.ui_dir / "vite.config.ts"
        self.assertTrue(vite_cfg.exists())
        content = vite_cfg.read_text(encoding="utf-8")
        self.assertIn("defineConfig", content)
        self.assertIn("/api", content)

        tsconfig = self.ui_dir / "tsconfig.json"
        self.assertTrue(tsconfig.exists())
        data = json.loads(tsconfig.read_text(encoding="utf-8"))
        self.assertEqual(data["compilerOptions"]["jsx"], "react-jsx")

    def test_tailwind_configs(self):
        tailwind_cfg = self.ui_dir / "tailwind.config.js"
        self.assertTrue(tailwind_cfg.exists())
        content = tailwind_cfg.read_text(encoding="utf-8")
        self.assertIn("./src/**/*.{js,ts,jsx,tsx}", content)

    def test_react_app_entry_files(self):
        index_html = self.ui_dir / "index.html"
        self.assertTrue(index_html.exists())

        main_tsx = self.ui_dir / "src" / "main.tsx"
        self.assertTrue(main_tsx.exists())

        app_tsx = self.ui_dir / "src" / "App.tsx"
        self.assertTrue(app_tsx.exists())
        app_content = app_tsx.read_text(encoding="utf-8")
        self.assertIn("Antinode Norma BDD Platform", app_content)


if __name__ == "__main__":
    unittest.main()
