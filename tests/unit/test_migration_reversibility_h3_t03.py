"""Unit tests for Phase H3 Task H3-T03: Migration Reversibility & Backup-First Gate."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from antinode_norma.core.backup import create_backup, restore_backup


class TestMigrationReversibilityH3T03(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

        self.db_path = self.temp_path / "norma.db"
        self.backup_path = self.temp_path / "backups" / "pre_destructive_backup.db"

        # Initialize v4 table schema
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE features (id TEXT PRIMARY KEY, title TEXT, legacy_col TEXT);")
        cursor.execute("INSERT INTO features VALUES ('f1', 'Login', 'legacy_data');")
        conn.commit()
        conn.close()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_backup_first_gate_and_destructive_migration_rollback(self):
        # 1. Backup-first gate prior to destructive migration
        backup_res = create_backup(db_path=self.db_path, backup_path=self.backup_path)
        self.assertEqual(backup_res["status"], "success")

        # 2. Execute destructive migration (e.g. drop legacy column)
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE features_v5 (id TEXT PRIMARY KEY, title TEXT);")
        cursor.execute("INSERT INTO features_v5 SELECT id, title FROM features;")
        cursor.execute("DROP TABLE features;")
        cursor.execute("ALTER TABLE features_v5 RENAME TO features;")
        conn.commit()

        # Confirm legacy column is gone
        cursor.execute("PRAGMA table_info(features);")
        columns = [row[1] for row in cursor.fetchall()]
        self.assertNotIn("legacy_col", columns)
        conn.close()

        # 3. Perform rollback restore from backup
        restore_res = restore_backup(backup_path=self.backup_path, db_path=self.db_path)
        self.assertEqual(restore_res["status"], "success")

        # 4. Assert restored state contains legacy column and data
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(features);")
        columns = [row[1] for row in cursor.fetchall()]
        self.assertIn("legacy_col", columns)

        cursor.execute("SELECT legacy_col FROM features WHERE id='f1';")
        self.assertEqual(cursor.fetchone()[0], "legacy_data")
        conn.close()


if __name__ == "__main__":
    unittest.main()
