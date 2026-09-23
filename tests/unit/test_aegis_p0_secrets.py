from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_secrets_strategy_has_template_exclusion_and_ci_scan() -> None:
    strategy = (REPOSITORY_ROOT / "docs" / "SECRETS.md").read_text(encoding="utf-8")
    gitignore = (REPOSITORY_ROOT / ".gitignore").read_text(encoding="utf-8")
    workflow = (REPOSITORY_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    assert "No Committed Secrets" in strategy
    assert "\n.env\n" in gitignore
    assert "gitleaks/gitleaks-action@v2" in workflow


def test_environment_template_contains_placeholders_not_credentials() -> None:
    template = (REPOSITORY_ROOT / ".env.example").read_text(encoding="utf-8")

    for key in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "OPENROUTER_API_KEY"):
        line = next(line for line in template.splitlines() if line.startswith(f"{key}="))
        assert line.split("=", 1)[1].strip().endswith("...")
