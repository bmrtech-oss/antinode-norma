"""Execution history persistence module for Norma BDD platform."""

import json
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional


@dataclass
class ExecutionHistoryRecord:
    """Record representing a single test execution run."""
    id: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    duration_seconds: float = 0.0
    status: str = "PASSED"  # PASSED, FAILED, DEGRADED
    total_scenarios: int = 0
    passed_scenarios: int = 0
    failed_scenarios: int = 0
    skipped_scenarios: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionHistoryRecord":
        return cls(**data)


class ExecutionHistoryStore:
    """Manages reading and writing execution history records to disk."""

    def __init__(self, history_file: str = "build/execution_history.json", database_url: Optional[str] = None):
        self.history_file = Path(history_file)
        self.database_url = database_url

    def save_run(self, record: ExecutionHistoryRecord) -> None:
        """Saves an execution history record to the JSON store."""
        if self.database_url:
            from antinode_norma.database import save_execution_history

            save_execution_history(self.database_url, record.to_dict())
            return
        history = self._load_all()
        history.append(record.to_dict())
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        self.history_file.write_text(json.dumps(history, indent=2), encoding="utf-8")

    def get_history(self, limit: Optional[int] = 50) -> List[ExecutionHistoryRecord]:
        """Retrieves recent execution history records, sorted newest first."""
        if self.database_url:
            from antinode_norma.database import load_execution_history

            records = [ExecutionHistoryRecord.from_dict(item) for item in load_execution_history(self.database_url)]
            records.sort(key=lambda r: r.timestamp, reverse=True)
            return records[:limit] if limit is not None and limit > 0 else records
        history_dicts = self._load_all()
        records = [ExecutionHistoryRecord.from_dict(d) for d in history_dicts]
        # Sort newest first based on timestamp
        records.sort(key=lambda r: r.timestamp, reverse=True)
        if limit is not None and limit > 0:
            return records[:limit]
        return records

    def _load_all(self) -> List[Dict[str, Any]]:
        """Loads all raw history dictionaries from the JSON store."""
        if not self.history_file.exists():
            return []
        try:
            data = json.loads(self.history_file.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
            return []
        except Exception:
            return []
