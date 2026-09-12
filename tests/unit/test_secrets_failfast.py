import pytest
from antinode_norma.utils.llm_factory import create_llm_callable


def test_missing_anthropic_api_key_raises_fail_fast(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(ValueError, match=r"Missing required secret ANTHROPIC_API_KEY.*\.env\.example"):
        create_llm_callable({"provider": "anthropic"})


def test_missing_openai_api_key_raises_fail_fast(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError, match=r"Missing required secret OPENAI_API_KEY.*\.env\.example"):
        create_llm_callable({"provider": "openai"})


def test_missing_openrouter_api_key_raises_fail_fast(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(ValueError, match=r"Missing required secret OPENROUTER_API_KEY.*\.env\.example"):
        create_llm_callable({"provider": "openrouter"})
