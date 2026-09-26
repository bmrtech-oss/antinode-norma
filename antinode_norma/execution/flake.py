import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel


class FlakeRecord(BaseModel):
    test_id: str
    total_runs: int = 0
    passed_runs: int = 0
    failed_runs: int = 0
    flake_rate: float = 0.0
    is_flaky: bool = False


class FlakeDetector:
    def __init__(self, storage_path: Optional[Path] = None, database_url: Optional[str] = None):
        self.database_url = database_url or os.getenv("DATABASE_URL")
        self.storage_path = storage_path or Path("build/flake_history.json")
        self.history: Dict[str, Dict[str, int]] = {}
        if self.database_url:
            from antinode_norma.database import load_flake_history, migrate

            migrate(self.database_url)
            self.history = load_flake_history(self.database_url)
        elif self.storage_path.exists():
            self._load_history()

    def _load_history(self) -> None:
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                self.history = json.load(f)
        except Exception:
            self.history = {}

    def _save_history(self) -> None:
        if self.database_url:
            return
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(self.history, f, indent=2)

    def record_run_result(self, test_id: str, passed: bool) -> None:
        if self.database_url:
            from antinode_norma.database import load_flake_history, record_flake_run

            record_flake_run(self.database_url, test_id, passed)
            self.history = load_flake_history(self.database_url)
            return

        if test_id not in self.history:
            self.history[test_id] = {"passed": 0, "failed": 0}

        if passed:
            self.history[test_id]["passed"] += 1
        else:
            self.history[test_id]["failed"] += 1

        self._save_history()

    def analyze_flakiness(self, threshold: float = 0.20) -> List[FlakeRecord]:
        records: List[FlakeRecord] = []
        for test_id, counts in self.history.items():
            p_cnt = counts.get("passed", 0)
            f_cnt = counts.get("failed", 0)
            total = p_cnt + f_cnt

            if total == 0:
                continue

            # A test is flaky if it has BOTH passed and failed runs (inconsistency)
            rate = min(p_cnt, f_cnt) / total if (p_cnt > 0 and f_cnt > 0) else 0.0
            is_flaky = rate >= threshold if (p_cnt > 0 and f_cnt > 0) else False

            record = FlakeRecord(
                test_id=test_id,
                total_runs=total,
                passed_runs=p_cnt,
                failed_runs=f_cnt,
                flake_rate=round(rate, 4),
                is_flaky=is_flaky,
            )
            records.append(record)

        return records
