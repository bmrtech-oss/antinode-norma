"""Unit tests for Phase 8 Task P8-T07: Execution History Store."""

import tempfile
import unittest
from pathlib import Path

from antinode_norma.execution.history import (
    ExecutionHistoryStore,
    ExecutionHistoryRecord,
)


class TestExecutionHistoryStore(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.history_file = Path(self.temp_dir.name) / "test_history.json"
        self.store = ExecutionHistoryStore(history_file=str(self.history_file))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_save_run_and_get_history(self):
        rec1 = ExecutionHistoryRecord(
            id="run-1",
            timestamp="2026-09-12T10:00:00+00:00",
            duration_seconds=1.5,
            status="PASSED",
            total_scenarios=5,
            passed_scenarios=5,
            failed_scenarios=0,
            metadata={"env": "staging"},
        )
        rec2 = ExecutionHistoryRecord(
            id="run-2",
            timestamp="2026-09-12T11:00:00+00:00",
            duration_seconds=2.0,
            status="FAILED",
            total_scenarios=5,
            passed_scenarios=4,
            failed_scenarios=1,
            metadata={"env": "staging"},
        )

        self.store.save_run(rec1)
        self.store.save_run(rec2)

        history = self.store.get_history(limit=50)
        self.assertEqual(len(history), 2)
        # Sorts newest first
        self.assertEqual(history[0].id, "run-2")
        self.assertEqual(history[1].id, "run-1")
        self.assertEqual(history[0].status, "FAILED")
        self.assertEqual(history[1].status, "PASSED")

    def test_history_limit(self):
        for i in range(10):
            rec = ExecutionHistoryRecord(
                id=f"run-{i}",
                timestamp=f"2026-09-12T10:{i:02d}:00+00:00",
            )
            self.store.save_run(rec)

        history = self.store.get_history(limit=3)
        self.assertEqual(len(history), 3)
        self.assertEqual(history[0].id, "run-9")

    def test_load_empty_or_corrupted_file(self):
        # Empty before file creation
        history = self.store.get_history()
        self.assertEqual(history, [])

        # Write corrupted JSON
        self.history_file.write_text("invalid json", encoding="utf-8")
        corrupted_history = self.store.get_history()
        self.assertEqual(corrupted_history, [])


if __name__ == "__main__":
    unittest.main()
