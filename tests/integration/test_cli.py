"""Integration tests for the CLI using the real LLM and file system."""

import subprocess
import sys
from pathlib import Path
import pytest


def _skip_on_transient_cli_failure(result):
    stderr = result.stderr.lower() if result.stderr else ""
    transient_markers = [
        "rate limit",
        "rate_limit",
        "service unavailable",
        "timeout",
        "connection error",
        "network error",
        "temporarily unavailable",
    ]
    if any(marker in stderr for marker in transient_markers):
        pytest.skip(
            f"Skipped due to transient LLM provider issue: {result.stderr.strip()}"
        )


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
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        _skip_on_transient_cli_failure(result)
    assert result.returncode == 0, f"CLI failed: {result.stderr}"
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
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        _skip_on_transient_cli_failure(result)
    assert result.returncode == 0
    assert "Quality score:" in result.stdout
    assert "Passes INVEST: True" in result.stdout
