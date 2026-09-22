from pathlib import Path


def test_release_checklist_exists_and_valid():
    checklist_path = Path("docs/RELEASE_CHECKLIST.md")
    assert checklist_path.exists(), "docs/RELEASE_CHECKLIST.md must exist"

    content = checklist_path.read_text(encoding="utf-8")

    assert "# NORMA-BDD Production Release Checklist" in content
    assert "Pre-Release Validation Items" in content
    assert "Release Sign-Off Matrix" in content

    required_items = [
        "Version & Changelog",
        "API Version Consistency",
        "Migration Round-Trip",
        "DR Restore Drill",
        "Observability Dashboard",
        "Regression Gate",
        "Score Re-Projection",
    ]

    for item in required_items:
        assert item in content, f"Missing required checklist item: {item}"
