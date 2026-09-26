from pathlib import Path

from antinode_norma.core.features import FeatureFlagResolver


def test_feature_flags_default_off_and_follow_documented_precedence(tmp_path, monkeypatch) -> None:
    config = tmp_path / "norma.config.yml"
    config.write_text("features:\n  unified_agent: true\n", encoding="utf-8")

    monkeypatch.setenv("NORMA_FEATURE_UNIFIED_AGENT", "false")
    resolver = FeatureFlagResolver(config_path=config, runtime_overrides={"unified_agent": True})

    assert resolver.is_enabled("unified_agent") is True
    assert resolver.is_enabled("cache_semantic") is False
    assert resolver.is_enabled("unified_agent", cli_override=False) is False


def test_malformed_feature_config_fails_closed_to_defaults(tmp_path) -> None:
    config = tmp_path / "norma.config.yml"
    config.write_text("features: [not-a-mapping", encoding="utf-8")

    resolver = FeatureFlagResolver(config_path=config)

    assert resolver.is_enabled("unified_agent") is False


def test_rollback_document_covers_flag_and_git_revert_paths() -> None:
    root = Path(__file__).resolve().parents[2]
    document = (root / "docs" / "ROLLBACK.md").read_text(encoding="utf-8")

    assert "NORMA_FEATURE_<NAME>=false" in document
    assert "git revert <commit-sha>" in document
    assert "Introduce" in document
    assert "Soak" in document
    assert "Retire" in document
