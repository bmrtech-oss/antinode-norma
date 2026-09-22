#!/usr/bin/env python3
"""Cross-track regression gate script for Antinode Norma platform.

Task H4-T01 (Phase H4 - Operational Maturity).
Executes unit test suite, walking skeleton smoke check, load test smoke, and backup/restore smoke check on every merge to main.
"""

import subprocess
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from antinode_norma.core.backup import create_backup, restore_backup
from tests.load.test_load import run_benchmark


def run_cross_track_regression_gate() -> bool:
    """Runs all 4 cross-track regression gate checks and returns True if all pass."""
    print("==================================================")
    print("Executing Antinode Norma Cross-Track Regression Gate (H4-T01)")
    print("==================================================")

    # 1. Unit Test Suite Smoke
    print("\n[Check 1/4] Running Unit Test Suite Smoke...")
    unit_res = subprocess.run([sys.executable, "-m", "pytest", "tests/unit/test_validator.py"], capture_output=True, text=True)
    if unit_res.returncode != 0:
        print(f"FAILED: Unit test suite check failed with output:\n{unit_res.stdout}\n{unit_res.stderr}")
        return False
    print("  ✓ Unit Test Suite Check PASSED")

    # 2. Walking Skeleton Smoke Check
    print("\n[Check 2/4] Running Walking Skeleton Smoke Check...")
    skeleton_res = subprocess.run([sys.executable, "-m", "pytest", "tests/unit/test_generate_and_autocorrect.py"], capture_output=True, text=True)
    if skeleton_res.returncode != 0:
        print(f"FAILED: Walking skeleton smoke check failed!")
        return False
    print("  ✓ Walking Skeleton Smoke Check PASSED")

    # 3. Load Test Smoke (10 users, read p95 < 300ms)
    print("\n[Check 3/4] Running Load Test Smoke...")
    load_res = run_benchmark(concurrent_users=10, total_requests=20)
    if not load_res.get("passes_read_threshold", False):
        print(f"FAILED: Load test smoke check failed p95 threshold! Results: {load_res}")
        return False
    print(f"  ✓ Load Test Smoke PASSED (p95: {load_res['p95_ms']} ms)")

    # 4. Backup & Restore Smoke Check
    print("\n[Check 4/4] Running Backup & Restore Smoke Check...")
    test_db = Path("build/regression_test_smoke.db")
    test_backup = Path("build/regression_test_backup.db")

    import sqlite3
    test_db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(test_db))
    conn.execute("CREATE TABLE smoke (id INT);")
    conn.execute("INSERT INTO smoke VALUES (1);")
    conn.commit()
    conn.close()

    b_res = create_backup(test_db, test_backup)
    r_res = restore_backup(test_backup, test_db)

    if test_db.exists():
        test_db.unlink()
    if test_backup.exists():
        test_backup.unlink()

    if b_res["status"] != "success" or r_res["status"] != "success":
        print(f"FAILED: Backup & Restore smoke check failed!")
        return False
    print("  ✓ Backup & Restore Smoke Check PASSED")

    print("\n==================================================")
    print("SUCCESS: All 4 Cross-Track Regression Gate Checks PASSED!")
    print("==================================================")
    return True


if __name__ == "__main__":
    if not run_cross_track_regression_gate():
        sys.exit(1)
