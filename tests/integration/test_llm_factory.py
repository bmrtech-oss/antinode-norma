"""Integration tests for LLM factory with OpenRouter."""

import os
import pytest
from antinode_norma.utils.llm_factory import create_llm_callable
from tests.conftest import maybe_skip_transient_llm_error


def get_generic_llm_config():
    if os.getenv("OPENROUTER_API_KEY"):
        return {
            "provider": "openrouter",
            "api_key": os.getenv("OPENROUTER_API_KEY"),
            "model": "openai/gpt-oss-120b:free",
            "base_url": "https://openrouter.ai/api/v1",
            "temperature": 0.2,
            "max_tokens": 100,
            "extra_body": {"provider": {"require_parameters": True}},
        }
    if os.getenv("OPENAI_API_KEY"):
        return {
            "provider": "openai",
            "api_key": os.getenv("OPENAI_API_KEY"),
            "model": "gpt-4o",
            "temperature": 0.2,
            "max_tokens": 100,
        }
    if os.getenv("ANTHROPIC_API_KEY"):
        return {
            "provider": "anthropic",
            "api_key": os.getenv("ANTHROPIC_API_KEY"),
            "model": "claude-3-5-sonnet-20241022",
            "temperature": 0.2,
            "max_tokens": 100,
        }
    raise RuntimeError("No LLM provider key configured")


@pytest.mark.external_integration
def test_llm_provider_call():
    config = get_generic_llm_config()
    llm = create_llm_callable(config)
    try:
        response = llm("What is the capital of France?")
    except Exception as exc:
        maybe_skip_transient_llm_error(exc)
        raise
    assert "Paris" in response or "paris" in response


@pytest.mark.external_integration
def test_llm_parser_integration():
    from antinode_norma.core.parser import parse_story

    config = get_generic_llm_config()
    config["max_tokens"] = 500
    llm = create_llm_callable(config)
    raw = "As a QA engineer, I want to automate tests so that we save time. Acceptance criteria: - Should run daily - Should report failures"
    try:
        story = parse_story(raw, llm)
    except Exception as exc:
        maybe_skip_transient_llm_error(exc)
        raise
    assert story.role
    assert story.action
    assert story.benefit
    assert story.acceptance_criteria
