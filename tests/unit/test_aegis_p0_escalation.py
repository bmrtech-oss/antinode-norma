from pathlib import Path


def test_escalation_policy_covers_adr_triggers_and_stop_rules() -> None:
    root = Path(__file__).resolve().parents[2]
    document = (root / "docs" / "ESCALATION.md").read_text(encoding="utf-8")

    required_terms = (
        "Plan Rejected Twice",
        "Verification Fails Twice",
        "Low-Confidence Judge Score",
        "Knowledge Graph Unavailable (Q11, production)",
        "Knowledge Graph Unavailable (Q11, development)",
        "Knowledge Graph Unavailable (Q12)",
        "Reuse Candidate Abandoned Upstream",
        "Tier 3 Task Should Be Tier 2",
        "build/escalation.json",
        ".github/ISSUE_TEMPLATE/blocked_task.md",
        "An agent stops after two rejected plans or two failed verification attempts.",
    )

    for term in required_terms:
        assert term in document


def test_blocked_task_template_captures_required_escalation_evidence() -> None:
    root = Path(__file__).resolve().parents[2]
    template = (
        root / ".github" / "ISSUE_TEMPLATE" / "blocked_task.md"
    ).read_text(encoding="utf-8")

    for term in (
        "Task ID:",
        "Escalation trigger:",
        "Evidence artifact:",
        "Remediation attempted",
        "Decision required",
        "Exit condition",
    ):
        assert term in template
