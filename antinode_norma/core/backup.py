"""Backup and Disaster Recovery module for Antinode Norma platform.

Task H2-T02 (Phase H2 - Enterprise Completeness).
Provides SQLite database snapshot backup via VACUUM INTO and restore functionality with verification.
"""

import shutil
import sqlite3
from pathlib import Path
from typing import Any, Dict


def create_backup(db_path: Path, backup_path: Path) -> Dict[str, Any]:
    """Creates a snapshot backup of SQLite database using VACUUM INTO.

    Args:
        db_path: Path to existing SQLite database.
        backup_path: Path where backup snapshot file will be created.

    Returns:
        Dict containing backup status, record counts, and metadata.
    """
    db_path = Path(db_path)
    backup_path = Path(backup_path)

    if not db_path.exists():
        return {"status": "error", "message": f"Database file not found: {db_path}"}

    backup_path.parent.mkdir(parents=True, exist_ok=True)
    if backup_path.exists():
        backup_path.unlink()

    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()
        # Query total tables as sanity check
        cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table';")
        table_count = cursor.fetchone()[0]

        # SQLite VACUUM INTO creates online consistent snapshot
        cursor.execute(f"VACUUM INTO '{backup_path.resolve()}';")
        conn.commit()
    finally:
        conn.close()

    # Verify backup database integrity
    backup_conn = sqlite3.connect(str(backup_path))
    try:
        backup_cursor = backup_conn.cursor()
        backup_cursor.execute("PRAGMA quick_check;")
        integrity = backup_cursor.fetchone()[0]
    finally:
        backup_conn.close()

    return {
        "status": "success" if integrity == "ok" else "failed",
        "integrity": integrity,
        "table_count": table_count,
        "backup_path": str(backup_path),
        "db_path": str(db_path),
    }


def restore_backup(backup_path: Path, db_path: Path) -> Dict[str, Any]:
    """Restores database from a backup snapshot.

    Args:
        backup_path: Path to backup snapshot file.
        db_path: Path where restored database should be placed.

    Returns:
        Dict containing restore status and verification result.
    """
    backup_path = Path(backup_path)
    db_path = Path(db_path)

    if not backup_path.exists():
        return {"status": "error", "message": f"Backup file not found: {backup_path}"}

    # Check backup integrity before restoring
    backup_conn = sqlite3.connect(str(backup_path))
    try:
        backup_cursor = backup_conn.cursor()
        backup_cursor.execute("PRAGMA quick_check;")
        integrity = backup_cursor.fetchone()[0]
        if integrity != "ok":
            return {"status": "error", "message": "Corrupted backup file"}

        backup_cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table';")
        table_count = backup_cursor.fetchone()[0]
    finally:
        backup_conn.close()

    db_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(backup_path, db_path)

    return {
        "status": "success",
        "table_count": table_count,
        "db_path": str(db_path),
        "backup_path": str(backup_path),
    }
