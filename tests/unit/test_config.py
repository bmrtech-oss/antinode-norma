"""Unit tests for configuration loading."""

from pathlib import Path

from dotenv import load_dotenv

from antinode_norma.core.config import NormaConfig, load_config


def test_env_loading():
    """Test that .env file is loaded (if present)."""
    load_dotenv()
    assert True


def test_load_default_norma_config():
    config = load_config(Path("non_existent.yml"))
    assert isinstance(config, NormaConfig)
    assert config.gates.min_soft_score == 0.85
    assert config.cache.cache_path == Path("build/llm_cache.json")
    assert config.governance.audit_enabled is False
    assert config.features["unified_agent"] is False
    assert config.aegis.enabled is False
    assert config.aegis.max_repair_attempts == 3


def test_load_custom_norma_config(tmp_path):
    custom_yaml = tmp_path / "norma.config.yml"
    custom_yaml.write_text(
        "aegis:\n  enabled: true\n  release_profile: aegis-foundation\n  max_repair_attempts: 5\n"
        "gates:\n  min_soft_score: 0.90\ncache:\n  exact: true\nfeatures:\n  unified_agent: true\n"
    )

    config = load_config(custom_yaml)
    assert config.gates.min_soft_score == 0.90
    assert config.cache.exact is True
    assert config.features["unified_agent"] is True
    assert config.aegis.enabled is True
    assert config.aegis.max_repair_attempts == 5
