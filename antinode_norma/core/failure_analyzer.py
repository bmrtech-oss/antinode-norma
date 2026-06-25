from __future__ import annotations

import json
import os
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

DB_FILE: Path = Path(
    os.getenv("ANTINODE_FAILURE_DB_FILE", Path.home() / ".antinode_norma_failures.db")
)
_TABLE_NAME = "failure_events"

_SELECTOR_PATTERNS = [
    r"locator\(['\"](.+?)['\"]\)",
    r"page\.locator\(['\"](.+?)['\"]\)",
    r"Selector:\s*['\"](.+?)['\"]",
    r"Unable to find element with selector ['\"](.+?)['\"]",
    r"['\"](#[^'\"]+)['\"]",
    r"['\"](text=[^'\"]+)['\"]",
]


@dataclass
class FailureEvent:
    step_text: Optional[str]
    test_title: str
    file_path: Optional[str]
    line: Optional[int]
    selector: Optional[str]
    error_message: str
    created_at: str


def _get_db_file() -> Path:
    return Path(os.getenv("ANTINODE_FAILURE_DB_FILE", str(DB_FILE)))


def set_db_file(path: Path | str) -> None:
    global DB_FILE
    DB_FILE = Path(path).expanduser()


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_get_db_file()), detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_database() -> None:
    with _get_connection() as conn:
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {_TABLE_NAME} (
                id INTEGER PRIMARY KEY,
                step_text TEXT,
                test_title TEXT NOT NULL,
                file_path TEXT,
                line INTEGER,
                selector TEXT,
                error_message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


def _extract_error_message(result: Dict[str, Any]) -> str:
    error = result.get("error")
    if isinstance(error, dict):
        return error.get("message") or json.dumps(error)
    if isinstance(error, list):
        return "\n".join(str(item) for item in error)
    if isinstance(error, str):
        return error
    return json.dumps(result)


def _extract_selector(text: str) -> Optional[str]:
    for pattern in _SELECTOR_PATTERNS:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    return None


def _read_snippet_from_file(file_path: str, line: Optional[int], context: int = 2) -> Optional[str]:
    if not file_path or line is None:
        return None
    try:
        path = Path(file_path)
        if not path.exists():
            return None
        lines = path.read_text(encoding="utf-8").splitlines()
        if not (1 <= line <= len(lines)):
            return None
        start = max(0, line - 1 - context)
        end = min(len(lines), line + context)
        return "\n".join(line.strip() for line in lines[start:end])
    except Exception:
        pass
    return None


def _infer_step_text_from_code(snippet: Optional[str]) -> Optional[str]:
    if not snippet:
        return None
    snippet = snippet.rstrip(";")
    if "steps." in snippet:
        match = re.search(r"(steps\.[A-Za-z0-9_]+\([^\n]*\))", snippet)
        if match:
            return match.group(1).strip()
        return snippet
    if "locator(" in snippet or ".locator(" in snippet:
        match = re.search(r"([A-Za-z0-9_\s\.-]*locator\([^\n]*\)[\s\S]*?)$", snippet)
        if match:
            return match.group(1).strip()
    return None


def _recursively_collect_tests(node: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    for test in node.get("tests", []):
        yield test
    for suite in node.get("suites", []):
        yield from _recursively_collect_tests(suite)


def parse_playwright_report(report_path: Path) -> List[FailureEvent]:
    data = json.loads(report_path.read_text(encoding="utf-8"))
    tests = list(_recursively_collect_tests(data))
    if not tests and isinstance(data, dict) and "tests" in data:
        tests = list(data.get("tests", []))

    failures: List[FailureEvent] = []
    for test in tests:
        for result in test.get("results", []):
            if result.get("status") != "failed":
                continue
            error_message = _extract_error_message(result)
            file_path = None
            line = None
            location = test.get("location") or result.get("location") or {}
            if isinstance(location, dict):
                file_path = location.get("file")
                line = location.get("line")
                if isinstance(line, str) and line.isdigit():
                    line = int(line)
                elif not isinstance(line, int):
                    line = None
            selector = _extract_selector(error_message)
            snippet = _read_snippet_from_file(file_path, line) if file_path else None
            step_text = _infer_step_text_from_code(snippet)
            failures.append(
                FailureEvent(
                    step_text=step_text,
                    test_title=test.get("title", "<unknown>"),
                    file_path=file_path,
                    line=line,
                    selector=selector,
                    error_message=error_message.strip(),
                    created_at="",
                )
            )
    return failures


def store_playwright_failures(report_path: Path) -> List[FailureEvent]:
    _ensure_database()
    failures = parse_playwright_report(report_path)
    if not failures:
        return []

    inserted: List[FailureEvent] = []
    with _get_connection() as conn:
        for failure in failures:
            conn.execute(
                f"INSERT INTO {_TABLE_NAME} (step_text, test_title, file_path, line, selector, error_message) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    failure.step_text,
                    failure.test_title,
                    failure.file_path,
                    failure.line,
                    failure.selector,
                    failure.error_message,
                ),
            )
            inserted.append(failure)
        conn.commit()

    return inserted


def _query_failures(where_clause: str, params: tuple[Any, ...], limit: int) -> List[FailureEvent]:
    _ensure_database()
    with _get_connection() as conn:
        cursor = conn.execute(
            f"SELECT step_text, test_title, file_path, line, selector, error_message, created_at"
            f" FROM {_TABLE_NAME} WHERE {where_clause} ORDER BY created_at DESC LIMIT ?",
            params + (limit,),
        )
        rows = cursor.fetchall()
    return [FailureEvent(**dict(row)) for row in rows]


def get_recent_failures(limit: int = 10) -> List[FailureEvent]:
    return _query_failures("1=1", (), limit)


def get_failure_examples_for_step(step_text: str, max_examples: int = 2) -> List[FailureEvent]:
    selector = _extract_selector(step_text)
    if selector:
        examples = _query_failures("selector = ?", (selector,), max_examples)
        if examples:
            return examples
        examples = _query_failures("selector LIKE ?", (f"%{selector}%",), max_examples)
        if examples:
            return examples

    exact_text_examples = _query_failures("step_text = ?", (step_text,), max_examples)
    if exact_text_examples:
        return exact_text_examples
    return _query_failures("step_text LIKE ?", (f"%{step_text}%",), max_examples)


def get_failure_suggestions_for_step(step_text: str, max_suggestions: int = 3) -> List[str]:
    selector = _extract_selector(step_text)
    if selector:
        failures = _query_failures("selector = ?", (selector,), max_suggestions)
    else:
        failures = _query_failures("step_text = ?", (step_text,), max_suggestions)

    suggestions: List[str] = []
    for failure in failures:
        summary_key = failure.selector or failure.step_text or failure.test_title
        error_line = failure.error_message.splitlines()[0]
        if selector:
            suggestions.append(
                f"Previous failure with selector '{summary_key}': {error_line}. Consider using a more robust selector, adding an explicit wait, or reordering the action."
            )
        else:
            suggestions.append(
                f"Previous failure for step '{summary_key}': {error_line}. Consider rephrasing the step or choosing a more specific locator."
            )
    return suggestions
