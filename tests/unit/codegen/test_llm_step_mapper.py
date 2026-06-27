import json

import pytest

from antinode_norma.core.failure_analyzer import FailureEvent
from antinode_norma.codegen.config import CodegenConfig
from antinode_norma.codegen.engine import llm_step_mapper
from antinode_norma.codegen.engine.rules import RuleEngine


@pytest.fixture(autouse=True)
def clear_llm_cache(monkeypatch, tmp_path):
    monkeypatch.setattr(
        llm_step_mapper,
        "_CACHE_FILE",
        tmp_path /
        "llm_step_cache.json")
    llm_step_mapper._CACHE.clear()
    llm_step_mapper._CACHE_ORDER.clear()
    yield
    llm_step_mapper._CACHE.clear()
    llm_step_mapper._CACHE_ORDER.clear()


def test_map_step_with_llm_returns_playwright_mapping(monkeypatch):
    async def fake_call(prompt: str, config: dict) -> str:
        return json.dumps(
            {
                "action": "NAVIGATE",
                "target": None,
                "value": "https://example.com/login",
                "options": {},
            }
        )

    monkeypatch.setattr(llm_step_mapper, "_call_llm", fake_call)
    action, target, value, options = llm_step_mapper.map_step(
        'Given I navigate to "https://example.com/login"',
        use_llm=True,
        fallback_to_rules=False,
    )

    assert action.name == "NAVIGATE"
    assert target is None
    assert value == "https://example.com/login"
    assert options == {}


def test_map_step_with_llm_understands_natural_language(monkeypatch):
    async def fake_call(prompt: str, config: dict) -> str:
        return json.dumps(
            {
                "action": "CLICK",
                "target": "text=reset link",
                "value": None,
                "options": {},
            }
        )

    monkeypatch.setattr(llm_step_mapper, "_call_llm", fake_call)
    action, target, value, options = llm_step_mapper.map_step(
        "When the user clicks the reset link in the email",
        use_llm=True,
        fallback_to_rules=False,
    )

    assert action.name == "CLICK"
    assert target == "text=reset link"
    assert value is None
    assert options == {}


def test_map_step_falls_back_to_rule_engine_when_llm_fails(monkeypatch):
    async def fake_call(prompt: str, config: dict) -> str:
        raise ValueError("LLM failure")

    monkeypatch.setattr(llm_step_mapper, "_call_llm", fake_call)

    action, target, value, options = llm_step_mapper.map_step(
        'Given I navigate to "https://example.com/login"',
        use_llm=True,
        fallback_to_rules=True,
    )

    assert action.name == "NAVIGATE"
    assert target is None
    assert value == "https://example.com/login"
    assert options == {}


def test_rule_engine_respects_codegen_base_url(monkeypatch):
    config = CodegenConfig(base_url="https://myapp.local")
    monkeypatch.setattr(
        "antinode_norma.codegen.engine.rules.get_config",
        lambda: config,
    )

    engine = RuleEngine()
    action, target, value, options = engine.map_step(
        "Given the user is on the login page")

    assert action.name == "NAVIGATE"
    assert value == "https://myapp.local/login"
    assert options == {}

    action, target, value, options = engine.map_step(
        "Given the user has successfully updated the password"
    )
    assert action.name == "NAVIGATE"
    assert value == "https://myapp.local"
    assert options == {}


def test_map_step_cache_prevents_duplicate_llm_calls(monkeypatch):
    call_count = {"count": 0}

    async def fake_call(prompt: str, config: dict) -> str:
        call_count["count"] += 1
        return json.dumps(
            {
                "action": "CLICK",
                "target": "#login-button",
                "value": None,
                "options": {},
            }
        )

    monkeypatch.setattr(llm_step_mapper, "_call_llm", fake_call)

    first = llm_step_mapper.map_step(
        'When I click on "#login-button"',
        use_llm=True,
        fallback_to_rules=False,
    )
    second = llm_step_mapper.map_step(
        'When I click on "#login-button"',
        use_llm=True,
        fallback_to_rules=False,
    )

    assert first == second
    assert call_count["count"] == 1
    assert llm_step_mapper._CACHE.get(
        'When I click on "#login-button"') is not None


def test_build_prompt_includes_failure_context(monkeypatch):
    failure = FailureEvent(
        step_text="await steps.clickElement(page, '#login-button')",
        test_title="User Login › click login",
        file_path=None,
        line=None,
        selector="#login-button",
        error_message="locator.click: waiting for locator('#login-button')",
        created_at="2026-06-25 00:00:00",
    )

    monkeypatch.setattr(
        llm_step_mapper,
        "get_failure_examples_for_step",
        lambda step_text, max_examples=2: [failure],
    )

    prompt = llm_step_mapper._build_prompt('When I click on "#login-button"')

    assert "Previous failure patterns to avoid:" in prompt
    assert "#login-button" in prompt


def test_build_prompt_skips_failure_context_when_disabled(monkeypatch):
    class DummyQuality:
        enable_failure_learning = False
        failure_learning_max_examples = 2

    monkeypatch.setattr(
        llm_step_mapper, "get_config", lambda: type(
            "C", (), {
                "quality": DummyQuality})())
    monkeypatch.setattr(
        llm_step_mapper,
        "get_failure_examples_for_step",
        lambda step_text,
        max_examples=2: [
            FailureEvent(
                step_text="await steps.clickElement(page, '#login-button')",
                test_title="User Login › click login",
                file_path=None,
                line=None,
                selector="#login-button",
                error_message="locator.click: waiting for locator('#login-button')",
                created_at="2026-06-25 00:00:00",
            )],
    )

    prompt = llm_step_mapper._build_prompt('When I click on "#login-button"')
    assert "Previous failure patterns to avoid:" not in prompt
