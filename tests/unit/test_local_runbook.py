"""
Unit tests for docs/LOCAL_RUNBOOK.md completeness and structure.
"""

from pathlib import Path


def test_local_runbook_exists_and_has_required_sections():
    runbook_path = Path("docs/LOCAL_RUNBOOK.md")
    assert runbook_path.exists(), "docs/LOCAL_RUNBOOK.md is missing."

    content = runbook_path.read_text(encoding="utf-8")
    assert len(content) > 1000, "docs/LOCAL_RUNBOOK.md is too short."

    required_sections = [
        "DISCOVER FIRST",
        "Dependency Inventory Table",
        "Feature-Flag Matrix",
        "Port Map",
        "Prerequisite Checklist",
        "§0. Prerequisites",
        "§1. Clone and Configure",
        "§2. Local Infrastructure",
        "§3. Database Setup",
        "§4. Application Setup",
        "§5. Walking Skeleton Smoke Test",
        "§6. UAT Checklist",
        "§7. Observability",
        "§8. Troubleshooting",
        "§9. Teardown",
        "§10. Promotion to Integration",
        "Gaps Found",
    ]

    for section in required_sections:
        assert section in content, f"Required section '{section}' is missing from docs/LOCAL_RUNBOOK.md."
