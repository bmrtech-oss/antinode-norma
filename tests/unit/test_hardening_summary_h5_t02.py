from pathlib import Path


def test_hardening_summary_exists_and_valid():
    summary_path = Path("docs/HARDENING_SUMMARY.md")
    assert summary_path.exists(), "docs/HARDENING_SUMMARY.md must exist"

    content = summary_path.read_text(encoding="utf-8")

    assert "# ADR-002 Post-Implementation Hardening Deliverables Summary" in content
    assert "Hardening Task Mapping Table" in content

    required_tasks = [f"H1-T0{i}" for i in range(1, 4)]
    required_tasks += [f"H2-T0{i}" for i in range(1, 7)]
    required_tasks += [f"H3-T0{i}" for i in range(1, 5)]
    required_tasks += [f"H4-T0{i}" for i in range(1, 4)]
    required_tasks += [f"H5-T0{i}" for i in range(1, 4)]

    for task_id in required_tasks:
        assert task_id in content, f"Missing required task ID in summary: {task_id}"


def test_architecture_has_adr002_references():
    arch_path = Path("docs/ARCHITECTURE.md")
    assert arch_path.exists(), "docs/ARCHITECTURE.md must exist"

    content = arch_path.read_text(encoding="utf-8")
    assert "Post-Implementation Hardening (ADR-002)" in content
    assert "docs/HARDENING_SUMMARY.md" in content
