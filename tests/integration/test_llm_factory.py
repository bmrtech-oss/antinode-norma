"""Integration tests for LLM factory with OpenRouter."""

import os
import pytest
from antinode_norma.utils.llm_factory import create_llm_callable

@pytest.mark.skipif(not os.getenv("OPENROUTER_API_KEY"), reason="OPENROUTER_API_KEY not set")
def test_openrouter_call():
    config = {
        "provider": "openrouter",
        "api_key": os.getenv("OPENROUTER_API_KEY"),
        "model": "openai/gpt-oss-120b:free",
        "base_url": "https://openrouter.ai/api/v1",
        "temperature": 0.2,
        "max_tokens": 100,
        "extra_body": {"provider": {"require_parameters": True}}
    }
    llm = create_llm_callable(config)
    response = llm("What is the capital of France?")
    assert "Paris" in response

@pytest.mark.skipif(not os.getenv("OPENROUTER_API_KEY"), reason="OPENROUTER_API_KEY not set")
def test_openrouter_parser_integration():
    from antinode_norma.core.parser import parse_story
    config = {
        "provider": "openrouter",
        "api_key": os.getenv("OPENROUTER_API_KEY"),
        "model": "openai/gpt-oss-120b:free",
        "base_url": "https://openrouter.ai/api/v1",
        "temperature": 0.2,
        "max_tokens": 500,
        "extra_body": {"provider": {"require_parameters": True}}
    }
    llm = create_llm_callable(config)
    raw = "As a QA engineer, I want to automate tests so that we save time. Acceptance criteria: - Should run daily - Should report failures"
    story = parse_story(raw, llm)
    assert story.role
    assert story.action
    assert story.benefit
    assert story.acceptance_criteria