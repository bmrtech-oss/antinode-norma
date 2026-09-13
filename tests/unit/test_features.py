from pathlib import Path
from antinode_norma.core.features import FeatureFlagResolver, DEFAULT_FEATURE_FLAGS


def test_feature_resolver_default_flags():
    resolver = FeatureFlagResolver(config_path=Path("non_existent.yml"))
    for flag_name, default_val in DEFAULT_FEATURE_FLAGS.items():
        assert resolver.is_enabled(flag_name) == default_val


def test_feature_resolver_config_override(tmp_path):
    config_file = tmp_path / "norma.config.yml"
    config_file.write_text("features:\n  unified_agent: true\n  cache_exact: false\n")

    resolver = FeatureFlagResolver(config_path=config_file)
    assert resolver.is_enabled("unified_agent") is True
    assert resolver.is_enabled("cache_exact") is False
    assert resolver.is_enabled("cache_semantic") is False


def test_feature_resolver_env_override(tmp_path, monkeypatch):
    config_file = tmp_path / "norma.config.yml"
    config_file.write_text("features:\n  unified_agent: false\n")

    monkeypatch.setenv("NORMA_FEATURE_UNIFIED_AGENT", "true")
    resolver = FeatureFlagResolver(config_path=config_file)
    assert resolver.is_enabled("unified_agent") is True


def test_feature_resolver_cli_override(tmp_path, monkeypatch):
    monkeypatch.setenv("NORMA_FEATURE_UNIFIED_AGENT", "true")
    resolver = FeatureFlagResolver(config_path=tmp_path / "norma.config.yml")
    assert resolver.is_enabled("unified_agent", cli_override=False) is False
