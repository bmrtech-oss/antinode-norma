"""Self-healing selector support for generated tests."""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

from ...utils.llm_factory import create_llm_callable

_LOGGER = logging.getLogger(__name__)
_CACHE_FILE = Path.home() / ".antinode_norma_healing_cache.json"
_CACHE: Dict[str, str] = {}
_CACHE_ORDER: list[str] = []
_DEFAULT_CACHE_SIZE = 1000


def _load_cache() -> None:
    if not _CACHE_FILE.exists():
        return
    try:
        payload = json.loads(_CACHE_FILE.read_text(encoding="utf-8"))
        entries = payload.get("entries", [])
        for entry in entries:
            key = entry.get("key")
            selector = entry.get("selector")
            if key and selector:
                _CACHE[key] = selector
                _CACHE_ORDER.append(key)
    except Exception as exc:
        _LOGGER.debug("Unable to load selector healing cache: %s", exc)


def _persist_cache() -> None:
    try:
        data = {"entries": [{"key": key, "selector": _CACHE[key]} for key in _CACHE_ORDER]}
        _CACHE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception as exc:
        _LOGGER.debug("Unable to persist selector healing cache: %s", exc)


def _cache_key(old_selector: str, step_context: str) -> str:
    return f"{old_selector.strip()}|{step_context.strip()}"


def _add_to_cache(key: str, selector: str, cache_size: int = _DEFAULT_CACHE_SIZE) -> None:
    if key in _CACHE_ORDER:
        _CACHE_ORDER.remove(key)
    _CACHE[key] = selector
    _CACHE_ORDER.append(key)
    while len(_CACHE_ORDER) > cache_size:
        oldest = _CACHE_ORDER.pop(0)
        _CACHE.pop(oldest, None)
    _persist_cache()


def _build_prompt(old_selector: str, step_context: str) -> str:
    examples = [
        {
            "old_selector": "#login-button",
            "step_context": "When the user clicks on the login button",
            "suggested_selector": "text=Login",
        },
        {
            "old_selector": "#email",
            "step_context": "And I fill the email address",
            "suggested_selector": '[data-testid="email"]',
        },
        {
            "old_selector": "#password",
            "step_context": "And I fill the password field",
            "suggested_selector": '[aria-label="Password"]',
        },
        {
            "old_selector": ".submit-btn",
            "step_context": "When I submit the form",
            "suggested_selector": 'role=button[name="Submit"]',
        },
    ]
    lines = [
        "You are an expert selector healing assistant.",
        "Suggest a repaired selector when the provided selector no longer matches.",
        "Only return a single selector string; do not include explanation.",
        "",
        "Examples:",
    ]
    for example in examples:
        lines.append(f"Old selector: {example['old_selector']}")
        lines.append(f"Step context: {example['step_context']}")
        lines.append(f"Suggested selector: {example['suggested_selector']}")
        lines.append("")
    lines.extend(
        [
            f"Old selector: {old_selector}",
            f"Step context: {step_context}",
            "Suggested selector:",
        ]
    )
    return "\n".join(lines)


def _build_llm_config_from_env() -> Dict[str, Any]:
    provider = os.getenv("LLM_PROVIDER", "anthropic").strip().lower() or "anthropic"
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


async def _suggest_alternative_selector(old_selector: str, step_context: str) -> str:
    config = _build_llm_config_from_env()
    prompt = _build_prompt(old_selector, step_context)
    raw = await _call_llm(prompt, config)
    suggestion = raw.strip().splitlines()[0].strip()
    if suggestion.startswith('"') and suggestion.endswith('"'):
        suggestion = suggestion[1:-1]
    return suggestion or old_selector


async def heal_selector(page: Any, old_selector: str, step_context: str) -> str:
    """Attempt to heal a missing selector using the page state and AI suggestions."""
    if not old_selector:
        return old_selector

    try:
        locator = page.locator(old_selector)
        if hasattr(locator, "count"):
            count = await locator.count()
            if count > 0:
                return old_selector
    except Exception:
        pass

    key = _cache_key(old_selector, step_context)
    if key in _CACHE:
        _LOGGER.debug("Selector healing cache hit for %s", key)
        return _CACHE[key]

    try:
        suggested = await _suggest_alternative_selector(old_selector, step_context)
        if suggested and suggested != old_selector:
            _add_to_cache(key, suggested)
            return suggested
    except Exception as exc:
        _LOGGER.debug("Selector healing LLM failed: %s", exc)

    return old_selector


def render_playwright_healer() -> str:
    return """import { Page } from '@playwright/test';

export async function healSelector(page: Page, selector: string, context: string): Promise<string> {
  try {
    await page.locator(selector).waitFor({ state: 'attached', timeout: 1000 });
    return selector;
  } catch (error) {
    console.warn(`Self-healing selector failed for ${selector}: ${context}`);
  }

  const normalized = context.trim().replace(/["'\\]/g, '');
  const candidates = [
    `text=${normalized}`,
    `[data-testid="${normalized}"]`,
    `[aria-label="${normalized}"]`,
    `[name="${normalized}"]`,
    `[title="${normalized}"]`,
    selector,
  ];

  for (const candidate of candidates) {
    try {
      const locator = page.locator(candidate);
      if ((await locator.count()) > 0) {
        console.info(`Selector healed: ${candidate}`);
        return candidate;
      }
    } catch {
      // ignore invalid selectors
    }
  }

  return selector;
}
"""


# Load cache eagerly so history is available across invocations.
_load_cache()
