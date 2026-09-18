from antinode_norma.core.types import TestCase
from antinode_norma.cache.exact import ExactPromptCache
from antinode_norma.core.agent import NormaAgent


def test_agent_cache_disabled_by_default(tmp_path, monkeypatch):
    monkeypatch.setenv("NORMA_FEATURE_CACHE_EXACT", "false")
    cache_file = tmp_path / "cache.json"
    cache = ExactPromptCache(cache_path=cache_file)

    calls = 0

    def mock_llm(prompt: str) -> str:
        nonlocal calls
        calls += 1
        return """
@TC-101
Feature: Login
  Scenario: Login test
    Given user opens login
"""

    tc = TestCase(id="TC-101", title="Login test")
    agent = NormaAgent(llm_callable=mock_llm, cache=cache)

    agent.generate_feature([tc])
    agent.generate_feature([tc])

    # Should call LLM twice when cache is disabled
    assert calls == 2


def test_agent_cache_enabled(tmp_path, monkeypatch):
    monkeypatch.setenv("NORMA_FEATURE_CACHE_EXACT", "true")
    cache_file = tmp_path / "cache.json"
    cache = ExactPromptCache(cache_path=cache_file)

    calls = 0

    def mock_llm(prompt: str) -> str:
        nonlocal calls
        calls += 1
        return """
@TC-101
Feature: Login
  Scenario: Login test
    Given user opens login
"""

    tc = TestCase(id="TC-101", title="Login test")
    agent = NormaAgent(llm_callable=mock_llm, cache=cache)

    res1, verdict1 = agent.generate_feature([tc])
    res2, verdict2 = agent.generate_feature([tc])

    # Should call LLM only once on cache hit
    assert calls == 1
    assert res1 == res2
    assert verdict1.hard_pass is True
    assert verdict2.hard_pass is True
