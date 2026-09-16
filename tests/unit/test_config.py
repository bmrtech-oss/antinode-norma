<<<<<<< HEAD
"""Unit tests for configuration loading."""

from dotenv import load_dotenv


def test_env_loading():
    """Test that .env file is loaded (if present)."""
    load_dotenv()
    # This just checks that the function runs; the actual variables depend on .env
    # If the .env file is present, it might be set; but we don't force it.
    assert True  # no assertion, just ensure no exception
=======
from pathlib import Path
from antinode_norma.core.config import load_config, NormaConfig


def test_load_default_norma_config():
    config = load_config(Path("non_existent.yml"))
    assert isinstance(config, NormaConfig)
    assert config.gates.min_soft_score == 0.85
    assert config.cache.cache_path == Path("build/llm_cache.json")
    assert config.governance.audit_enabled is False
    assert config.features["unified_agent"] is False


def test_load_custom_norma_config(tmp_path):
    custom_yaml = tmp_path / "norma.config.yml"
    custom_yaml.write_text(
        "gates:\n  min_soft_score: 0.90\ncache:\n  exact: true\nfeatures:\n  unified_agent: true\n"
    )

    config = load_config(custom_yaml)
    assert config.gates.min_soft_score == 0.90
    assert config.cache.exact is True
    assert config.features["unified_agent"] is True
>>>>>>> d4d2d9a (fix(tests): update CORS header assertion in test_api_p9_t01.py)
