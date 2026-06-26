#!/usr/bin/env python3
"""
Test script for antinode-norma CLI.

This script runs the `anorm generate` command with a sample user story
and verifies that a feature file is successfully generated.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# Story that meets INVEST criteria
TEST_STORY = (
    "As a registered user, I want to reset my password via email so that "
    "I can regain access to my account. "
    "Acceptance criteria: "
    "- The system should send a password reset link to the user's registered email. "
    "- The user should be able to click the link and set a new password. "
    "- The system should display an error message when an invalid token is used. "
    "- The system should expire the reset link after 30 minutes."
)


def main():
    print("=== Testing antinode-norma CLI ===\n")
    print("Using story:")
    print(TEST_STORY)
    print()

    # Build the command
    cmd = [sys.executable, "-m", "antinode_norma.cli", "generate", TEST_STORY]

    print(f"Running: {' '.join(cmd)}\n")

    # Run the CLI and capture output
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120, cwd=os.getcwd(), env=os.environ.copy()
        )
    except subprocess.TimeoutExpired:
        print("ERROR: Command timed out after 120 seconds.")
        sys.exit(1)

    # Print stdout and stderr for debugging
    print("STDOUT:")
    print(result.stdout)
    if result.stderr:
        print("STDERR:")
        print(result.stderr)

    # Check return code
    if result.returncode != 0:
        print(f"\nERROR: Command failed with return code {result.returncode}")
        sys.exit(1)

    # Verify output contains success message
    if "Feature file written" not in result.stdout:
        print("ERROR: Success message not found in output.")
        sys.exit(1)

    # Extract the file path from the output
    lines = result.stdout.strip().split("\n")
    feature_path = None
    for line in lines:
        if "Feature file written:" in line:
            feature_path = line.split("Feature file written:")[-1].strip()
            break

    if not feature_path:
        print("ERROR: Could not parse feature file path from output.")
        sys.exit(1)

    # Verify the file exists
    full_path = Path(feature_path)
    if not full_path.exists():
        print(f"ERROR: Feature file not found at {full_path}")
        sys.exit(1)

    # Read and print first few lines of the file for confirmation
    print(f"\nFeature file created at: {full_path}")
    print("\n--- First 10 lines of feature file ---")
    with open(full_path, "r") as f:
        lines = f.readlines()
    for line in lines[:10]:
        print(line.rstrip())
    if len(lines) > 10:
        print("...")

    print("\n✅ Test passed! The CLI generated a valid feature file.")
    sys.exit(0)


if __name__ == "__main__":
    main()
