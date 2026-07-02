"""Self-healing selector support for generated tests."""

import asyncio
import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from ...utils.llm_factory import create_llm_callable
from ..engine.exceptions import SelectorNotFoundError

_LOGGER = logging.getLogger(__name__)
_CACHE_FILE = Path.home() / ".antinode_norma_healing_cache.json"
_CACHE: Dict[str, str] = {}
_CACHE_ORDER: List[str] = []
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
        data = {
            "entries": [{"key": key, "selector": _CACHE[key]} for key in _CACHE_ORDER]
        }
        _CACHE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception as exc:
        _LOGGER.debug("Unable to persist selector healing cache: %s", exc)


def _normalize_cache_key(old_selector: str, step_context: str) -> str:
    return f"{old_selector.strip()}|{step_context.strip()}"


@dataclass
class SelectorHealingResult:
    selector: str
    confidence: float
    source: str
    strategy: str
    step_context: str
    cache_hit: bool = False


class SelectorHealer:
    def __init__(self, cache_file: Optional[Path] = None, cache_size: int = _DEFAULT_CACHE_SIZE):
        self.cache_file = cache_file or _CACHE_FILE
        self.cache_size = cache_size
        if cache_file is None:
            self.cache = _CACHE
            self.cache_order = _CACHE_ORDER
        else:
            self.cache = {}
            self.cache_order = []
        self._load_cache()

    def _load_cache(self) -> None:
        if not self.cache_file.exists():
            return

        try:
            payload = json.loads(self.cache_file.read_text(encoding="utf-8"))
            entries = payload.get("entries", [])
            for entry in entries:
                key = entry.get("key")
                selector = entry.get("selector")
                if key and selector:
                    self.cache[key] = selector
                    self.cache_order.append(key)
        except Exception as exc:
            _LOGGER.debug("Unable to load selector healing cache: %s", exc)

    def _persist_cache(self) -> None:
        try:
            data = {
                "entries": [{"key": key, "selector": self.cache[key]} for key in self.cache_order]
            }
            self.cache_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as exc:
            _LOGGER.debug("Unable to persist selector healing cache: %s", exc)

    def _cache_key(self, old_selector: str, step_context: str) -> str:
        return _normalize_cache_key(old_selector, step_context)

    def _add_to_cache(self, key: str, selector: str) -> None:
        if key in self.cache_order:
            self.cache_order.remove(key)
        self.cache[key] = selector
        self.cache_order.append(key)
        while len(self.cache_order) > self.cache_size:
            oldest = self.cache_order.pop(0)
            self.cache.pop(oldest, None)
        self._persist_cache()

    def _build_prompt(self, old_selector: str, step_context: str) -> str:
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
        lines.extend([
            f"Old selector: {old_selector}",
            f"Step context: {step_context}",
            "Suggested selector:",
        ])
        return "\n".join(lines)

    def _build_llm_config_from_env(self) -> Dict[str, Any]:
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

    async def _call_llm(self, prompt: str, config: Dict[str, Any]) -> str:
        llm = create_llm_callable(config)
        return await asyncio.to_thread(llm, prompt)

    async def _suggest_alternative_selector(self, old_selector: str, step_context: str) -> str:
        config = self._build_llm_config_from_env()
        prompt = self._build_prompt(old_selector, step_context)
        raw = await self._call_llm(prompt, config)
        suggestion = raw.strip().splitlines()[0].strip()
        if suggestion.startswith('"') and suggestion.endswith('"'):
            suggestion = suggestion[1:-1]
        return suggestion or old_selector

    async def _try_direct_locator(self, page: Any, selector: str) -> bool:
        try:
            locator = page.locator(selector)
            if hasattr(locator, "count"):
                count = await locator.count()
                return count > 0
        except Exception:
            pass
        return False

    def _build_candidate_selectors(self, old_selector: str, step_context: str) -> List[str]:
        normalized_context = step_context.strip().replace('"', "").replace("'", "").lower()
        candidates = [old_selector]
        if normalized_context:
            candidates.extend([
                f"text={normalized_context}",
                f"[data-testid=\"{normalized_context}\"]",
                f"[aria-label=\"{normalized_context}\"]",
                f"[name=\"{normalized_context}\"]",
                f"[title=\"{normalized_context}\"]",
            ])
        return candidates

    async def heal_selector(self, page: Any, old_selector: str, step_context: str) -> SelectorHealingResult:
        if not old_selector:
            return SelectorHealingResult(
                selector=old_selector,
                confidence=1.0,
                source="noop",
                strategy="no_selector",
                step_context=step_context,
            )

        if await self._try_direct_locator(page, old_selector):
            return SelectorHealingResult(
                selector=old_selector,
                confidence=1.0,
                source="direct",
                strategy="unchanged",
                step_context=step_context,
            )

        cache_key = self._cache_key(old_selector, step_context)
        if cache_key in self.cache:
            candidate = self.cache[cache_key]
            if await self._try_direct_locator(page, candidate):
                _LOGGER.info("Selector healing cache hit for %s -> %s", old_selector, candidate)
                return SelectorHealingResult(
                    selector=candidate,
                    confidence=0.95,
                    source="cache",
                    strategy="cached_alternative",
                    step_context=step_context,
                    cache_hit=True,
                )

        for candidate in self._build_candidate_selectors(old_selector, step_context):
            if candidate == old_selector:
                continue
            if await self._try_direct_locator(page, candidate):
                _LOGGER.info("Selector healed by DOM candidate: %s -> %s", old_selector, candidate)
                self._add_to_cache(cache_key, candidate)
                return SelectorHealingResult(
                    selector=candidate,
                    confidence=0.82,
                    source="dom_similarity",
                    strategy="candidate_search",
                    step_context=step_context,
                )

        try:
            suggested = await self._suggest_alternative_selector(old_selector, step_context)
            if suggested and suggested != old_selector and await self._try_direct_locator(page, suggested):
                self._add_to_cache(cache_key, suggested)
                _LOGGER.info("Selector healed by LLM: %s -> %s", old_selector, suggested)
                return SelectorHealingResult(
                    selector=suggested,
                    confidence=0.75,
                    source="llm",
                    strategy="llm_fallback",
                    step_context=step_context,
                )
        except SelectorNotFoundError:
            raise
        except Exception as exc:
            _LOGGER.debug("Selector healing LLM failed: %s", exc)

        raise SelectorNotFoundError(
            old_selector,
            step_context,
            alternatives=[
                "Try a role= or text= based locator",
                "Prefer a data-testid or aria-label selector",
            ],
        ) from None


async def heal_selector(page: Any, old_selector: str, step_context: str) -> str:
    healer = SelectorHealer()
    result = await healer.heal_selector(page, old_selector, step_context)
    if result.confidence >= 0.8:
        return result.selector
    raise SelectorNotFoundError(
        old_selector,
        step_context,
        alternatives=[
            f"Best candidate: {result.selector}",
            "Review the selector manually if it does not match the intended element.",
        ],
    )


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
