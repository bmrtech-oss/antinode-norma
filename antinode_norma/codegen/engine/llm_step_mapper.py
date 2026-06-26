"""LLM-backed mapping of Gherkin steps to Playwright actions."""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

import os
from antinode_norma.core.failure_analyzer import get_failure_examples_for_step
from ...utils.llm_factory import create_llm_callable
from ..config import get_config
from ..models.test_model import ActionType
from .rules import RuleEngine

_LOGGER = logging.getLogger(__name__)
_CACHE_FILE = Path.home() / ".antinode_norma_llm_step_cache.json"
_CACHE: Dict[str, Tuple[ActionType, Optional[str], Optional[str], Dict[str, Any]]] = {}
_CACHE_ORDER: list[str] = []


def _normalize_action(action_value: str) -> ActionType:
    if not isinstance(action_value, str) or not action_value.strip():
        raise ValueError("LLM response missing 'action' field")

    normalized = action_value.strip().upper().replace(" ", "_")
    try:
        return ActionType[normalized]
    except KeyError as exc:
        raise ValueError(f"Unsupported action from LLM: {action_value}") from exc


def _build_prompt(step_text: str) -> str:
    examples = [
        (
            'Given I navigate to "https://example.com/login"',
            {
                "action": "NAVIGATE",
                "target": None,
                "value": "https://example.com/login",
                "options": {},
            },
        ),
        (
            'When I click on "#login-button"',
            {"action": "CLICK", "target": "#login-button", "value": None, "options": {}},
        ),
        (
            'Then I should see "Welcome"',
            {"action": "ASSERT_TEXT", "target": None, "value": "Welcome", "options": {}},
        ),
        (
            'When I fill "test@example.com" into "#email"',
            {"action": "FILL", "target": "#email", "value": "test@example.com", "options": {}},
        ),
        (
            'When I double click "#item"',
            {"action": "DOUBLE_CLICK", "target": "#item", "value": None, "options": {}},
        ),
        (
            'When I right click on "#menu"',
            {"action": "RIGHT_CLICK", "target": "#menu", "value": None, "options": {}},
        ),
        (
            'When I hover over "#tooltip-trigger"',
            {"action": "HOVER", "target": "#tooltip-trigger", "value": None, "options": {}},
        ),
        (
            'When I clear "#search"',
            {"action": "CLEAR", "target": "#search", "value": None, "options": {}},
        ),
        (
            'When I select "United States" from "#country"',
            {"action": "SELECT", "target": "#country", "value": "United States", "options": {}},
        ),
        (
            'When I check "#subscribe"',
            {"action": "CHECK", "target": "#subscribe", "value": None, "options": {}},
        ),
        (
            'When I uncheck "#subscribe"',
            {"action": "UNCHECK", "target": "#subscribe", "value": None, "options": {}},
        ),
        (
            'Then "#spinner" should be visible',
            {"action": "ASSERT_VISIBLE", "target": "#spinner", "value": None, "options": {}},
        ),
        (
            'Then "#spinner" should not be visible',
            {"action": "ASSERT_HIDDEN", "target": "#spinner", "value": None, "options": {}},
        ),
        (
            'Then I should see "Account created"',
            {"action": "ASSERT_TEXT", "target": None, "value": "Account created", "options": {}},
        ),
        (
            'Then the value of "#price" should be "19.99"',
            {"action": "ASSERT_VALUE", "target": "#price", "value": "19.99", "options": {}},
        ),
        (
            'Then the URL should be "https://example.com/dashboard"',
            {
                "action": "ASSERT_URL",
                "target": None,
                "value": "https://example.com/dashboard",
                "options": {},
            },
        ),
        (
            'Then the title should contain "Dashboard"',
            {"action": "ASSERT_TITLE", "target": None, "value": "Dashboard", "options": {}},
        ),
        (
            "And I wait for 5 seconds",
            {"action": "WAIT", "target": None, "value": "5", "options": {}},
        ),
        (
            "When I take a screenshot",
            {"action": "SCREENSHOT", "target": None, "value": None, "options": {}},
        ),
        (
            'When I execute script "return window.location.href"',
            {
                "action": "EXECUTE_SCRIPT",
                "target": None,
                "value": "return window.location.href",
                "options": {},
            },
        ),
    ]

    prompt_lines = [
        "You are a test automation expert converting Gherkin steps to Playwright actions.",
        "",
        "Examples:",
    ]

    for gherkin, playwright in examples:
        prompt_lines.append(f'Gherkin: "{gherkin}"')
        prompt_lines.append(f"Playwright: {json.dumps(playwright)}")
        prompt_lines.append("")

    quality = get_config().quality
    failure_examples = []
    if quality.enable_failure_learning:
        failure_examples = get_failure_examples_for_step(
            step_text,
            max_examples=quality.failure_learning_max_examples,
        )
    if failure_examples:
        prompt_lines.append("")
        prompt_lines.append("Previous failure patterns to avoid:")
        for failure in failure_examples:
            summary = failure.selector or failure.step_text or failure.test_title
            error_line = failure.error_message.splitlines()[0]
            prompt_lines.append(f"- {summary}: {error_line}")
        prompt_lines.append("")
        prompt_lines.append(
            "Prefer more robust selectors or alternative mappings when a similar failure is detected."
        )

    prompt_lines.extend(
        [
            "Now convert this step to Playwright:",
            f'Gherkin: "{step_text}"',
            "Playwright:",
        ]
    )

    return "\n".join(prompt_lines)


def _extract_json_object(raw: str) -> str:
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("LLM response does not contain a valid JSON object")
    return raw[start : end + 1]


def _parse_llm_output(raw: str) -> Dict[str, Any]:
    payload = raw.strip()
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        payload = _extract_json_object(raw)
        try:
            return json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ValueError(f"LLM returned invalid JSON: {exc}") from exc


def _cache_key(step_text: str) -> str:
    return step_text.strip()


def _load_persistent_cache() -> None:
    if not _CACHE_FILE.exists():
        return

    try:
        payload = json.loads(_CACHE_FILE.read_text(encoding="utf-8"))
        entries = payload.get("entries", [])
        for entry in entries:
            step = entry.get("step_text")
            mapping = entry.get("mapping")
            if not step or not isinstance(mapping, dict):
                continue
            try:
                action = _normalize_action(mapping.get("action", ""))
            except ValueError:
                continue
            target = mapping.get("target")
            value = mapping.get("value")
            options = mapping.get("options") or {}
            if not isinstance(options, dict):
                options = {}
            _CACHE[step] = (action, target, value, options)
            _CACHE_ORDER.append(step)
    except Exception as exc:
        _LOGGER.debug("Unable to load LLM cache from %s: %s", _CACHE_FILE, exc)


def _persist_cache() -> None:
    data = {
        "entries": [
            {
                "step_text": step,
                "mapping": {
                    "action": mapping[0].name,
                    "target": mapping[1],
                    "value": mapping[2],
                    "options": mapping[3],
                },
            }
            for step, mapping in zip(_CACHE_ORDER, (_CACHE[step] for step in _CACHE_ORDER))
        ]
    }
    try:
        _CACHE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception as exc:
        _LOGGER.debug("Unable to persist LLM cache to %s: %s", _CACHE_FILE, exc)


def _add_to_cache(
    step_text: str, mapping: Tuple[ActionType, Optional[str], Optional[str], Dict[str, Any]]
) -> None:
    key = _cache_key(step_text)
    quality = get_config().quality
    if key in _CACHE_ORDER:
        _CACHE_ORDER.remove(key)
    _CACHE[key] = mapping
    _CACHE_ORDER.append(key)

    while len(_CACHE_ORDER) > quality.llm_mapping_cache_size:
        oldest = _CACHE_ORDER.pop(0)
        _CACHE.pop(oldest, None)

    _persist_cache()


def _build_llm_config_from_env() -> Dict[str, Any]:
    provider = os.getenv("LLM_PROVIDER", "anthropic").strip().lower()
    if not provider:
        provider = "anthropic"

    return {
        "provider": provider,
        "api_key": os.getenv("ANTHROPIC_API_KEY")
        or os.getenv("OPENAI_API_KEY")
        or os.getenv("OPENROUTER_API_KEY"),
        "model": os.getenv("LLM_MODEL") or None,
        "temperature": float(os.getenv("LLM_TEMPERATURE", "0.2")),
        "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "1024")),
        "base_url": os.getenv("LLM_BASE_URL"),
        "url": os.getenv("LLM_URL"),
        "extra_body": {},
    }


async def _call_llm(prompt: str, config: Dict[str, Any]) -> str:
    llm = create_llm_callable(config)
    return await asyncio.to_thread(llm, prompt)


async def map_step_with_llm(
    step_text: str,
) -> Tuple[ActionType, Optional[str], Optional[str], Dict[str, Any]]:
    key = _cache_key(step_text)
    if key in _CACHE:
        _LOGGER.debug("LLM cache hit for step: %s", key)
        return _CACHE[key]

    quality = get_config().quality
    prompt = _build_prompt(step_text)
    llm_config = _build_llm_config_from_env()
    timeout = quality.llm_mapping_timeout if quality.llm_mapping_timeout else 5

    raw_output = None
    try:
        _LOGGER.debug("Calling LLM for step mapping: %s", step_text)
        raw_output = await asyncio.wait_for(_call_llm(prompt, llm_config), timeout=timeout)
        mapping = _parse_llm_output(raw_output)
    except Exception as exc:
        _LOGGER.debug("LLM mapping failed on first attempt for '%s': %s", step_text, exc)
        retry_prompt = (
            prompt
            + "\n\nIMPORTANT: Please respond with valid JSON only. The JSON object must include action, target, value, and options."
        )
        try:
            raw_output = await asyncio.wait_for(
                _call_llm(retry_prompt, llm_config), timeout=timeout
            )
            mapping = _parse_llm_output(raw_output)
        except Exception as retry_exc:
            raise ValueError(
                f"LLM mapping failed for step '{step_text}'. Raw output: {raw_output!r}. Error: {retry_exc}"
            ) from retry_exc

    if not isinstance(mapping, dict):
        raise ValueError("LLM response must be a JSON object")

    action = _normalize_action(mapping.get("action") or mapping.get("Action") or "")
    target = mapping.get("target") if mapping.get("target") is not None else None
    value = mapping.get("value") if mapping.get("value") is not None else None
    options = mapping.get("options") or {}
    if not isinstance(options, dict):
        options = {}

    result = (action, target, value, options)
    _add_to_cache(key, result)
    return result


def map_step(
    step_text: str,
    use_llm: bool = True,
    fallback_to_rules: bool = True,
    fallback_engine: Optional[RuleEngine] = None,
    interactive_callback: Optional[
        Callable[
            [str, str, list[str]], Tuple[ActionType, Optional[str], Optional[str], Dict[str, Any]]
        ]
    ] = None,
) -> Tuple[ActionType, Optional[str], Optional[str], Dict[str, Any]]:
    if not use_llm:
        return (fallback_engine or RuleEngine()).map_step(step_text)

    key = _cache_key(step_text)
    if key in _CACHE:
        _LOGGER.debug("LLM cache hit for step: %s", key)
        return _CACHE[key]

    try:
        return asyncio.run(map_step_with_llm(step_text))
    except Exception as exc:
        _LOGGER.debug("LLM mapping error for '%s': %s", step_text, exc)
        if fallback_to_rules:
            _LOGGER.debug("Falling back to RuleEngine for step: %s", step_text)
            try:
                return (fallback_engine or RuleEngine()).map_step(step_text)
            except ValueError as rules_exc:
                if interactive_callback is not None:
                    _LOGGER.debug("Invoking interactive callback for step: %s", step_text)
                    return interactive_callback(step_text, str(rules_exc), [])
                raise
        if interactive_callback is not None:
            _LOGGER.debug("Invoking interactive callback after LLM failure for step: %s", step_text)
            return interactive_callback(step_text, str(exc), [])
        raise


# Load cache at import time so it is persistent across runs.
_load_persistent_cache()
