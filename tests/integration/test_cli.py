"""Integration tests for the CLI using the real LLM and file system."""

import os
import subprocess
import sys
from pathlib import Path
import pytest

from tests.conftest import is_transient_llm_error_message


def _run_cli(cmd, timeout=60):
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        timeout=timeout,
    )


def _skip_on_transient_cli_failure(result):
    output = "\n".join([result.stderr or "", result.stdout or ""])
    if is_transient_llm_error_message(output):
        pytest.skip(f"Skipped due to transient LLM provider issue: {output.strip()}")


@pytest.mark.external_integration
def test_cli_generate(sample_story_pass, tmp_features):
    """Test that the CLI generates a feature file."""
    cmd = [
        sys.executable,
        "-m",
        "antinode_norma.cli",
        "generate",
        sample_story_pass,
        "--output-dir",
        str(tmp_features),
    ]
    result = _run_cli(cmd, timeout=120)
    if result.returncode != 0:
        _skip_on_transient_cli_failure(result)
    assert result.returncode == 0, (
        f"CLI failed ({result.returncode}): stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert "Feature file written" in result.stdout

    # Extract file path from output
    for line in result.stdout.splitlines():
        if "Feature file written:" in line:
            path = line.split(":", 1)[1].strip()
            feature_file = Path(path)
            assert feature_file.exists()
            assert feature_file.stat().st_size > 0
            break
    else:
        pytest.fail("No feature file path found in output")


@pytest.mark.external_integration
def test_cli_quality_only(sample_story_pass):
    cmd = [
        sys.executable,
        "-m",
        "antinode_norma.cli",
        "generate",
        "--quality-only",
        sample_story_pass,
    ]
    result = _run_cli(cmd, timeout=60)
    if result.returncode != 0:
        _skip_on_transient_cli_failure(result)
    assert result.returncode == 0, (
        f"CLI failed ({result.returncode}): stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert "Quality score:" in result.stdout
    assert "Passes INVEST: True" in result.stdout
