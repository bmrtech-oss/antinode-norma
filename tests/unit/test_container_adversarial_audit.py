"""
Unit tests for docs/CONTAINER_ADVERSARIAL_AUDIT.md audit report completeness.
"""

from pathlib import Path


def test_container_adversarial_audit_doc_exists():
    doc_path = Path("docs/CONTAINER_ADVERSARIAL_AUDIT.md")
    assert doc_path.exists(), "docs/CONTAINER_ADVERSARIAL_AUDIT.md is missing."

    content = doc_path.read_text(encoding="utf-8")
    assert len(content) > 1000, "docs/CONTAINER_ADVERSARIAL_AUDIT.md is too short."

    required_sections = [
        "Verdict Summary",
        "Adversarial Audit Matrix (13 Methods)",
        "Top 3 Critical Findings & One-Line Remediations",
        "Detailed Method Breakdown",
        "Method 1: Secret Leak in Image History",
        "Method 2: Non-Root Execution",
        "Method 4: Healthcheck Theater",
        "Method 6: Migration Race Condition",
        "Method 9: Volume Permissions under Rootless Podman",
    ]

    for section in required_sections:
        assert section in content, f"Required section '{section}' missing from CONTAINER_ADVERSARIAL_AUDIT.md"
