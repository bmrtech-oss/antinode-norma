"""Capture a reproducible repository and test baseline for ADR-003 P1-T01."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _run(command: list[str], root: Path) -> str:
    result = subprocess.run(
        command,
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def collect_baseline(root: Path) -> dict[str, Any]:
    """Collect source revision, interpreter, and collected pytest count."""

    commit_sha = _run(["git", "rev-parse", "HEAD"], root)
    collection_output = _run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "--no-cov"],
        root,
    )
    collected_line = next(
        (line for line in collection_output.splitlines() if "test" in line and "collected" in line),
        None,
    )
    if collected_line is None:
        raise RuntimeError("pytest collection output did not contain a test count")

    test_count = int(collected_line.split()[0])
    return {
        "baseline_version": 1,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "commit_sha": commit_sha,
        "python_version": sys.version.split()[0],
        "pytest_command": f"{sys.executable} -m pytest --collect-only -q --no-cov",
        "collected_test_count": test_count,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    baseline = collect_baseline(args.root.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(baseline, indent=2) + "\n", encoding="utf-8")
    print(f"Baseline written: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
