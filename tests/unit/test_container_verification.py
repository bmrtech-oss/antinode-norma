"""
Unit tests for docs/CONTAINER_VERIFICATION.md audit report completeness.
"""

from pathlib import Path


def test_container_verification_doc_exists():
    doc_path = Path("docs/CONTAINER_VERIFICATION.md")
    assert doc_path.exists(), "docs/CONTAINER_VERIFICATION.md is missing."

    content = doc_path.read_text(encoding="utf-8")
    assert len(content) > 1000, "docs/CONTAINER_VERIFICATION.md is too short."

    required_sections = [
        "Verdict Summary",
        "Pass 0 — Runtime Detection & Parity Map",
        "Pass 1 — Dockerfile Portability Audit",
        "Pass 2 — Compose Portability Audit",
        "Pass 3 — Cold-Start Under Docker",
        "Pass 4 — Cold-Start Under Podman",
        "Pass 5 — Parity Table",
        "Blockers & Gaps Found",
        "Recommended Next Action",
    ]

    for section in required_sections:
        assert section in content, f"Required section '{section}' missing from CONTAINER_VERIFICATION.md"
