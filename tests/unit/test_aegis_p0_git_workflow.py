from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_git_workflow_documents_branch_commit_pr_and_release_controls() -> None:
    document = (REPOSITORY_ROOT / "docs" / "GIT_WORKFLOW.md").read_text(encoding="utf-8")

    for required_text in (
        "Branching Strategy",
        "Commit Message Convention",
        "Pull Request & CI Gate Requirements",
        "task/<PHASE>-<TASK-ID>-<slug>",
        "gitleaks",
        "Cost Gate check",
        "repository settings",
    ):
        assert required_text in document


def test_git_workflow_targets_existing_ci_checks() -> None:
    document = (REPOSITORY_ROOT / "docs" / "GIT_WORKFLOW.md").read_text(encoding="utf-8")
    ci = (REPOSITORY_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    assert "norma-bdd" in document
    assert "gitleaks/gitleaks-action@v2" in ci
    assert "branches: [ main, develop ]" in ci
