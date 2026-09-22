"""Unit tests for Phase H2 Task H2-T01: v4 -> v5 Data Migration."""

import tempfile
import unittest
from pathlib import Path

from antinode_norma.core.migrate_v4 import migrate_v4_data


class TestMigrateV4(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.source_dir = Path(self.temp_dir.name)

        # Create v4 config
        config_path = self.source_dir / "norma.config.yml"
        config_path.write_text("llm:\n  provider: openai\n", encoding="utf-8")

        # Create 3 v4 features
        features_dir = self.source_dir / "features"
        features_dir.mkdir(parents=True, exist_ok=True)
        for i in range(1, 4):
            (features_dir / f"feature_{i}.feature").write_text(f"Feature: Test {i}\n", encoding="utf-8")

        # Create 5 v4 stories
        stories_dir = self.source_dir / "stories"
        stories_dir.mkdir(parents=True, exist_ok=True)
        for i in range(1, 6):
            (stories_dir / f"story_{i}.md").write_text(f"Story {i}\n", encoding="utf-8")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_dry_run_mode(self):
        res = migrate_v4_data(source_dir=self.source_dir, dry_run=True)
        self.assertEqual(res["status"], "success")
        self.assertTrue(res["dry_run"])
        self.assertEqual(res["features_migrated"], 3)
        self.assertEqual(res["stories_migrated"], 5)
        self.assertTrue(res["config_migrated"])

    def test_idempotency_and_migration(self):
        # Run 1
        res1 = migrate_v4_data(source_dir=self.source_dir, dry_run=False)
        self.assertEqual(res1["status"], "success")
        self.assertEqual(res1["features_migrated"], 3)
        self.assertEqual(res1["stories_migrated"], 5)

        # Run 2 (Idempotency)
        res2 = migrate_v4_data(source_dir=self.source_dir, dry_run=False)
        self.assertEqual(res2["status"], "success")
        self.assertEqual(res2["features_migrated"], 3)
        self.assertEqual(res2["stories_migrated"], 5)


if __name__ == "__main__":
    unittest.main()
