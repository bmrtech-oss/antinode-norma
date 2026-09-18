from antinode_norma.core.types import TestCase
from antinode_norma.cache.semantic import SemanticPromptCache
from antinode_norma.core.agent import NormaAgent


def test_semantic_cache_similarity_matching(tmp_path):
    cache_file = tmp_path / "sem_cache.json"
    cache = SemanticPromptCache(cache_path=cache_file, similarity_threshold=0.8)

    prompt1 = "Generate a BDD feature file for user login with password"
    prompt2 = "Generate a BDD feature file for user login with a password"  # Minor variation (adds "a")
    different_prompt = "Export sales report to Excel spreadsheet format"

    response1 = "Feature: User Login\n  Scenario: Login"

    cache.set(prompt1, response1)

    # Similar prompt should hit cache
    match = cache.get(prompt2)
    assert match is not None
    assert match[0] == response1
    assert match[1] >= 0.8

    # Completely different prompt should miss
    assert cache.get(different_prompt) is None


def test_semantic_cache_agent_integration(tmp_path, monkeypatch):
    monkeypatch.setenv("NORMA_FEATURE_CACHE_SEMANTIC", "true")
    cache_file = tmp_path / "sem_cache.json"
    cache = SemanticPromptCache(cache_path=cache_file, similarity_threshold=0.8)

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

    tc1 = TestCase(id="TC-101", title="Login test")
    agent = NormaAgent(llm_callable=mock_llm, cache=cache)

    res1, verdict1 = agent.generate_feature([tc1])
    res2, verdict2 = agent.generate_feature([tc1])

    # Should call LLM only once on semantic hit
    assert calls == 1
    assert res1 == res2
    assert verdict1.hard_pass is True
