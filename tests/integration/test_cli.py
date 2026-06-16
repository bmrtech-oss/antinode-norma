"""Integration tests for the CLI using the real LLM and file system."""

import subprocess
import sys
from pathlib import Path
import pytest
from tests.conftest import has_openrouter_key


@pytest.mark.skipif(not has_openrouter_key(), reason="OPENROUTER_API_KEY not set")
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


@pytest.mark.skipif(not has_openrouter_key(), reason="OPENROUTER_API_KEY not set")
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
    assert result.returncode == 0
    assert "Quality score:" in result.stdout
    assert "Passes INVEST: True" in result.stdout
