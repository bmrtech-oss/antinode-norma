"""
Persistent feedback store for mapping decisions and test results.

Stores mapping outcomes (pass/fail/skipped) to enable:
- Success rate tracking for selectors
- Similarity-based retrieval of proven mappings
- Learning loop for continuous improvement
"""

import hashlib
import json
import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


@dataclass
class FeedbackRecord:
    """A record of a mapping decision and its test outcome."""

    mapping_id: str  # Hash of step_text + selector for uniqueness
    step_text: str
    action_type: str
    selector: str
    test_result: str  # 'pass', 'fail', 'skipped'
    execution_context: Dict[str, Any]  # {browser, page, datetime, error_msg}
    timestamp: str
    mapping_source: str = "unknown"  # rule_engine, llm, similarity, interactive
    confidence: float = 0.0


class FeedbackStore:
    """SQLite-backed persistent feedback store."""

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize feedback store.

        Args:
            db_path: Path to SQLite database. If None, uses ~/.antinode_norma/feedback.db
        """
        if db_path is None:
            db_path = Path.home() / ".antinode_norma" / "feedback.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self._conn = None
        self._init_schema()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close connection."""
        self.close()

    def close(self):
        """Close the database connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def _init_schema(self):
        """Create tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY,
                    mapping_id TEXT UNIQUE,
                    step_text TEXT,
                    action_type TEXT,
                    selector TEXT,
                    test_result TEXT,
                    execution_context TEXT,
                    mapping_source TEXT DEFAULT 'unknown',
                    confidence REAL DEFAULT 0.0,
                    timestamp TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS selector_stats (
                    id INTEGER PRIMARY KEY,
                    selector TEXT UNIQUE,
                    action_type TEXT,
                    pass_count INTEGER DEFAULT 0,
                    fail_count INTEGER DEFAULT 0,
                    skip_count INTEGER DEFAULT 0,
                    last_used TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_step_text ON feedback(step_text)
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_selector ON feedback(selector)
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_test_result ON feedback(test_result)
                """
            )
            conn.commit()

    @staticmethod
    def _make_mapping_id(step_text: str, selector: str) -> str:
        """Generate unique ID for a mapping."""
        content = f"{step_text}|{selector}".encode()
        return hashlib.sha256(content).hexdigest()[:16]

    def record_result(
        self,
        step_text: str,
        selector: str,
        action_type: str,
        test_result: str,
        execution_context: Optional[Dict[str, Any]] = None,
        mapping_source: str = "unknown",
        confidence: float = 0.0,
    ) -> FeedbackRecord:
        """
        Record a mapping decision and test outcome.

        Args:
            step_text: Original step text (e.g., "click the login button")
            selector: Generated selector
            action_type: Action type (e.g., "click", "type", "navigate")
            test_result: Outcome ('pass', 'fail', 'skipped')
            execution_context: Optional metadata (browser, page, error_msg, etc.)
            mapping_source: Source of mapping (rule_engine, llm, similarity, interactive)
            confidence: Confidence score of original mapping (0.0-1.0)

        Returns:
            FeedbackRecord
        """
        if execution_context is None:
            execution_context = {}
        execution_context.setdefault("timestamp", datetime.utcnow().isoformat())

        mapping_id = self._make_mapping_id(step_text, selector)
        timestamp = datetime.utcnow().isoformat()

        record = FeedbackRecord(
            mapping_id=mapping_id,
            step_text=step_text,
            action_type=action_type,
            selector=selector,
            test_result=test_result,
            execution_context=execution_context,
            timestamp=timestamp,
            mapping_source=mapping_source,
            confidence=confidence,
        )

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO feedback
                    (mapping_id, step_text, action_type, selector, test_result,
                     execution_context, mapping_source, confidence, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        mapping_id,
                        step_text,
                        action_type,
                        selector,
                        test_result,
                        json.dumps(execution_context),
                        mapping_source,
                        confidence,
                        timestamp,
                    ),
                )

                # Update selector stats
                cursor.execute(
                    """
                    INSERT INTO selector_stats
                    (selector, action_type, last_used)
                    VALUES (?, ?, ?)
                    ON CONFLICT(selector) DO UPDATE SET last_used = ?
                    """,
                    (selector, action_type, timestamp, timestamp),
                )

                # Increment pass/fail counter
                if test_result == "pass":
                    cursor.execute(
                        "UPDATE selector_stats SET pass_count = pass_count + 1 WHERE selector = ?",
                        (selector,),
                    )
                elif test_result == "fail":
                    cursor.execute(
                        "UPDATE selector_stats SET fail_count = fail_count + 1 WHERE selector = ?",
                        (selector,),
                    )
                elif test_result == "skipped":
                    cursor.execute(
                        "UPDATE selector_stats SET skip_count = skip_count + 1 WHERE selector = ?",
                        (selector,),
                    )

                conn.commit()
                logger.debug(f"Recorded feedback for mapping {mapping_id}: {test_result}")
        except sqlite3.Error as e:
            logger.error(f"Failed to record feedback: {e}")
            raise

        return record

    def get_success_rate(self, selector: str) -> float:
        """
        Get success rate for a selector.

        Args:
            selector: Selector string

        Returns:
            Success rate as float (0.0-1.0), or 0.0 if no history
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT pass_count, fail_count, skip_count FROM selector_stats
                    WHERE selector = ?
                    """,
                    (selector,),
                )
                row = cursor.fetchone()
                if not row:
                    return 0.0

                pass_count, fail_count, skip_count = row
                total = pass_count + fail_count
                if total == 0:
                    return 0.0
                return pass_count / total
        except sqlite3.Error as e:
            logger.error(f"Failed to get success rate: {e}")
            return 0.0

    def get_results_for_selector(self, selector: str, limit: int = 10) -> List[FeedbackRecord]:
        """
        Get all feedback records for a selector.

        Args:
            selector: Selector string
            limit: Maximum number of records to return

        Returns:
            List of FeedbackRecord
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT * FROM feedback WHERE selector = ?
                    ORDER BY timestamp DESC LIMIT ?
                    """,
                    (selector, limit),
                )
                rows = cursor.fetchall()
                records = []
                for row in rows:
                    records.append(
                        FeedbackRecord(
                            mapping_id=row["mapping_id"],
                            step_text=row["step_text"],
                            action_type=row["action_type"],
                            selector=row["selector"],
                            test_result=row["test_result"],
                            execution_context=json.loads(row["execution_context"] or "{}"),
                            timestamp=row["timestamp"],
                            mapping_source=row["mapping_source"],
                            confidence=row["confidence"],
                        )
                    )
                return records
        except sqlite3.Error as e:
            logger.error(f"Failed to get results for selector: {e}")
            return []

    def get_results_for_step(self, step_text: str, limit: int = 10) -> List[FeedbackRecord]:
        """
        Get all feedback records for a step text.

        Args:
            step_text: Step text
            limit: Maximum number of records to return

        Returns:
            List of FeedbackRecord
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT * FROM feedback WHERE step_text = ?
                    ORDER BY timestamp DESC LIMIT ?
                    """,
                    (step_text, limit),
                )
                rows = cursor.fetchall()
                records = []
                for row in rows:
                    records.append(
                        FeedbackRecord(
                            mapping_id=row["mapping_id"],
                            step_text=row["step_text"],
                            action_type=row["action_type"],
                            selector=row["selector"],
                            test_result=row["test_result"],
                            execution_context=json.loads(row["execution_context"] or "{}"),
                            timestamp=row["timestamp"],
                            mapping_source=row["mapping_source"],
                            confidence=row["confidence"],
                        )
                    )
                return records
        except sqlite3.Error as e:
            logger.error(f"Failed to get results for step: {e}")
            return []

    def get_passing_results(self, action_type: Optional[str] = None, limit: int = 50) -> List[FeedbackRecord]:
        """
        Get all passing feedback records.

        Args:
            action_type: Optional filter by action type (e.g., 'click', 'type')
            limit: Maximum number of records to return

        Returns:
            List of FeedbackRecord sorted by most recent
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                if action_type:
                    cursor.execute(
                        """
                        SELECT * FROM feedback 
                        WHERE test_result = 'pass' AND action_type = ?
                        ORDER BY timestamp DESC LIMIT ?
                        """,
                        (action_type, limit),
                    )
                else:
                    cursor.execute(
                        """
                        SELECT * FROM feedback 
                        WHERE test_result = 'pass'
                        ORDER BY timestamp DESC LIMIT ?
                        """,
                        (limit,),
                    )
                rows = cursor.fetchall()
                records = []
                for row in rows:
                    records.append(
                        FeedbackRecord(
                            mapping_id=row["mapping_id"],
                            step_text=row["step_text"],
                            action_type=row["action_type"],
                            selector=row["selector"],
                            test_result=row["test_result"],
                            execution_context=json.loads(row["execution_context"] or "{}"),
                            timestamp=row["timestamp"],
                            mapping_source=row["mapping_source"],
                            confidence=row["confidence"],
                        )
                    )
                return records
        except sqlite3.Error as e:
            logger.error(f"Failed to get passing results: {e}")
            return []

    def clear_all(self):
        """Clear all feedback data (for testing)."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM feedback")
                cursor.execute("DELETE FROM selector_stats")
                conn.commit()
                logger.info("Cleared all feedback data")
        except sqlite3.Error as e:
            logger.error(f"Failed to clear feedback: {e}")
            raise

    def export_json(self, output_path: Path):
        """Export feedback records to JSON."""
        try:
            records = self.get_passing_results(limit=10000)
            data = [asdict(r) for r in records]
            with open(output_path, "w") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Exported {len(data)} records to {output_path}")
        except Exception as e:
            logger.error(f"Failed to export feedback: {e}")
            raise
