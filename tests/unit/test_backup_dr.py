"""Unit tests for Phase H2 Task H2-T02: Backup and Disaster Recovery."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from antinode_norma.core.backup import create_backup, restore_backup


class TestBackupAndDR(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

        self.db_path = self.temp_path / "norma.db"
        self.backup_path = self.temp_path / "backups" / "norma_backup.db"

        # Initialize test database
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE users (id TEXT PRIMARY KEY, username TEXT);")
        cursor.execute("INSERT INTO users VALUES ('u1', 'alice');")
        cursor.execute("INSERT INTO users VALUES ('u2', 'bob');")
        conn.commit()
        conn.close()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_create_and_restore_backup(self):
        # 1. Create backup
        backup_res = create_backup(db_path=self.db_path, backup_path=self.backup_path)
        self.assertEqual(backup_res["status"], "success")
        self.assertTrue(self.backup_path.exists())

        # 2. Modify database (disaster scenario)
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users;")
        conn.commit()
        cursor.execute("SELECT count(*) FROM users;")
        self.assertEqual(cursor.fetchone()[0], 0)
        conn.close()

        # 3. Restore database from backup
        restore_res = restore_backup(backup_path=self.backup_path, db_path=self.db_path)
        self.assertEqual(restore_res["status"], "success")

        # 4. Verify data recovery
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM users;")
        self.assertEqual(cursor.fetchone()[0], 2)
        conn.close()


if __name__ == "__main__":
    unittest.main()
