"""Unit tests for Phase 9 Task P9-T04: Feature Review Page Component."""

import unittest
from pathlib import Path


class TestUIFeatureReviewPage(unittest.TestCase):
    def setUp(self):
        self.ui_dir = Path("ui")

    def test_feature_review_component_exists(self):
        comp = self.ui_dir / "src" / "components" / "FeatureReview.tsx"
        self.assertTrue(comp.exists())

        content = comp.read_text(encoding="utf-8")
        self.assertIn("export default function FeatureReview", content)
        self.assertIn("/api/features", content)
        self.assertIn("run_gates=true", content)
        self.assertIn("Gherkin Source Text", content)

    def test_app_integration(self):
        app = self.ui_dir / "src" / "App.tsx"
        self.assertTrue(app.exists())

        content = app.read_text(encoding="utf-8")
        self.assertIn("import FeatureReview from './components/FeatureReview'", content)
        self.assertIn("Feature Review", content)


if __name__ == "__main__":
    unittest.main()
