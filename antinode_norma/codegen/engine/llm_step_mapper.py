"""LLM-backed mapping of Gherkin steps to Playwright actions."""

import asyncio
import json
import logging
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

import os
from antinode_norma.core.failure_analyzer import get_failure_examples_for_step
from ...utils.llm_factory import create_llm_callable
from ..config import get_config
from ..models.test_model import ActionType
from .exceptions import LLMTimeoutError, StepMappingError
from .feedback_store import FeedbackStore
from .rules import RuleEngine

_LOGGER = logging.getLogger(__name__)
_CACHE_FILE = Path.home() / ".antinode_norma_llm_step_cache.json"
_CACHE: Dict[str, Tuple[ActionType, Optional[str], Optional[str], Dict[str, Any]]] = {}
_CACHE_ORDER: list[str] = []


@dataclass
class SelectorCandidate:
    """A selector variant with priority and scoring."""

    value: str  # The actual selector
    priority: int  # Priority order (lower is higher priority)
    readability: float  # 0.0-1.0 based on syntax simplicity
    reason: str  # Why this candidate was generated


@dataclass
class MappingResult:
    action_type: ActionType
    selector: Optional[str] = None
    value: Optional[str] = None
    options: Optional[Dict[str, Any]] = None
    confidence: float = 0.0
    source: str = "rule_engine"
    reason: Optional[str] = None
    step_text: Optional[str] = None
    selector_candidates: Optional[list[SelectorCandidate]] = None

    def to_tuple(self) -> Tuple[ActionType, Optional[str], Optional[str], Dict[str, Any]]:
        return self.action_type, self.selector, self.value, self.options or {}


class SelectorGenerator:
    """Generate selector alternatives and score them by readability/priority."""

    PRIORITY_ORDER = {
        "data-testid": 1,
        "aria-label": 2,
        "role": 3,
        "text": 4,
        "css": 5,
        "xpath": 6,
    }

    @staticmethod
    def _extract_testid(selector: str) -> Optional[str]:
        """Extract data-testid value if present."""
        match = re.search(r'data-testid=["\']?([^"\'>\]]+)["\']?', selector)
        return match.group(1) if match else None

    @staticmethod
    def _extract_aria_label(selector: str) -> Optional[str]:
        """Extract aria-label value if present."""
        match = re.search(r'aria-label=["\']?([^"\'>\]]+)["\']?', selector)
        return match.group(1) if match else None

    @staticmethod
    def _extract_role(selector: str) -> Optional[str]:
        """Extract role value if present."""
        match = re.search(r'role=["\']?([^"\'>\]]+)["\']?', selector)
        return match.group(1) if match else None

    @staticmethod
    def _get_readability_score(selector: str) -> float:
        """Score selector readability (0.0-1.0)."""
        if not selector:
            return 0.0
        
        # Prefer shorter, attribute-based selectors
        length_penalty = min(len(selector) / 100.0, 1.0)  # Normalize length
        
        # Check for stability indicators
        stability_bonus = 0.0
        if "data-testid" in selector:
            stability_bonus += 0.3
        elif "aria-label" in selector:
            stability_bonus += 0.25
        elif "role=" in selector:
            stability_bonus += 0.2
        elif "id=" in selector:
            stability_bonus += 0.15
        elif "//" in selector:  # XPath penalty
            stability_bonus -= 0.2
        
        return min(1.0, (1.0 - length_penalty * 0.3 + stability_bonus))

    @classmethod
    def generate_alternatives(cls, selector: Optional[str]) -> list[SelectorCandidate]:
        """
        Generate selector alternatives from a primary selector.

        Args:
            selector: Primary selector string

        Returns:
            List of SelectorCandidate with priority ordering
        """
        if not selector:
            return []

        candidates = []
        
        # Always include the original first
        original_score = cls._get_readability_score(selector)
        candidates.append(
            SelectorCandidate(
                value=selector,
                priority=0,
                readability=original_score,
                reason="Original selector from mapping",
            )
        )

        # Generate data-testid variant if not already present
        testid = cls._extract_testid(selector)
        if testid:
            candidates.append(
                SelectorCandidate(
                    value=f"[data-testid='{testid}']",
                    priority=1,
                    readability=0.95,
                    reason="data-testid attribute (most stable)",
                )
            )

        # Generate aria-label variant if not already present
        aria_label = cls._extract_aria_label(selector)
        if aria_label:
            candidates.append(
                SelectorCandidate(
                    value=f"[aria-label='{aria_label}']",
                    priority=2,
                    readability=0.90,
                    reason="aria-label attribute (semantic)",
                )
            )

        # Generate role variant if not already present
        role = cls._extract_role(selector)
        if role:
            candidates.append(
                SelectorCandidate(
                    value=f"[role='{role}']",
                    priority=3,
                    readability=0.85,
                    reason="role attribute (accessible)",
                )
            )

        # If selector contains text-based matching, suggest as alternative
        if ":has-text(" in selector or "text=" in selector:
            # Already text-based, no need for alternative
            pass
        elif len(candidates) < 3:  # Only add synthetic variants if we don't have enough
            # Try to suggest a CSS variant (already in original likely)
            pass

        # Sort by priority, then by readability (descending)
        candidates.sort(key=lambda c: (c.priority, -c.readability))
        
        return candidates


def _normalize_action(
    action_value: str, step_text: Optional[str] = None
) -> ActionType:
    if not isinstance(action_value, str) or not action_value.strip():
        raise StepMappingError(
            step_text or "unknown step",
            "LLM response missing 'action' field",
            ["Ensure the response includes an action such as CLICK, FILL, or ASSERT_TEXT."],
        )

    normalized = action_value.strip().upper().replace(" ", "_")
    try:
        return ActionType[normalized]
    except KeyError as exc:
        raise StepMappingError(
            step_text or "unknown step",
            f"Unsupported action from LLM: {action_value}",
            ["Use one of the supported Playwright actions in the response."],
        ) from exc


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
            {
                "action": "CLICK",
                "target": "#login-button",
                "value": None,
                "options": {},
            },
        ),
        (
            'Then I should see "Welcome"',
            {
                "action": "ASSERT_TEXT",
                "target": None,
                "value": "Welcome",
                "options": {},
            },
        ),
        (
            'When I fill "test@example.com" into "#email"',
            {
                "action": "FILL",
                "target": "#email",
                "value": "test@example.com",
                "options": {},
            },
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
            {
                "action": "HOVER",
                "target": "#tooltip-trigger",
                "value": None,
                "options": {},
            },
        ),
        (
            'When I clear "#search"',
            {"action": "CLEAR", "target": "#search", "value": None, "options": {}},
        ),
        (
            'When I select "United States" from "#country"',
            {
                "action": "SELECT",
                "target": "#country",
                "value": "United States",
                "options": {},
            },
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
            {
                "action": "ASSERT_VISIBLE",
                "target": "#spinner",
                "value": None,
                "options": {},
            },
        ),
        (
            'Then "#spinner" should not be visible',
            {
                "action": "ASSERT_HIDDEN",
                "target": "#spinner",
                "value": None,
                "options": {},
            },
        ),
        (
            'Then I should see "Account created"',
            {
                "action": "ASSERT_TEXT",
                "target": None,
                "value": "Account created",
                "options": {},
            },
        ),
        (
            'Then the value of "#price" should be "19.99"',
            {
                "action": "ASSERT_VALUE",
                "target": "#price",
                "value": "19.99",
                "options": {},
            },
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
            {
                "action": "ASSERT_TITLE",
                "target": None,
                "value": "Dashboard",
                "options": {},
            },
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


def _extract_json_object(raw: str, step_text: Optional[str] = None) -> str:
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise StepMappingError(
            step_text or "unknown step",
            "LLM response does not contain a valid JSON object",
            ["Return a single JSON object with action, target, value, and options."],
        )
    return raw[start : end + 1]


def _parse_llm_output(raw: str, step_text: Optional[str] = None) -> Dict[str, Any]:
    payload = raw.strip()
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        payload = _extract_json_object(raw, step_text)
        try:
            return json.loads(payload)
        except json.JSONDecodeError as exc:
            raise StepMappingError(
                step_text or "unknown step",
                f"LLM returned invalid JSON: {exc}",
                ["Ensure the model replies with valid JSON only."],
            ) from exc


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
                action = _normalize_action(mapping.get("action", ""), step)
            except StepMappingError:
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
            for step, mapping in zip(
                _CACHE_ORDER, (_CACHE[step] for step in _CACHE_ORDER)
            )
        ]
    }
    try:
        _CACHE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception as exc:
        _LOGGER.debug("Unable to persist LLM cache to %s: %s", _CACHE_FILE, exc)


def _add_to_cache(
    step_text: str,
    mapping: Tuple[ActionType, Optional[str], Optional[str], Dict[str, Any]],
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


def _build_llm_config_from_env(provider: Optional[str] = None) -> Dict[str, Any]:
    selected_provider = (provider or os.getenv("LLM_PROVIDER", "anthropic")).strip().lower()
    if not selected_provider:
        selected_provider = "anthropic"

    return {
        "provider": selected_provider,
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


class LLMStepMapper(RuleEngine):
    """Rule-first, LLM-backed, similarity-assisted step mapper."""

    def __init__(
        self,
        provider: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        llm_timeout: Optional[int] = None,
        similarity_threshold: float = 0.55,
        feedback_store: Optional[FeedbackStore] = None,
    ):
        super().__init__()
        self.provider = provider or getattr(config or {}, "get", lambda *_: None)("provider")
        if not self.provider:
            quality = getattr(get_config(), "quality", None)
            self.provider = getattr(quality, "llm_provider", None) or os.getenv(
                "LLM_PROVIDER", "anthropic"
            )
        self.provider = str(self.provider or "anthropic").strip().lower()
        self.llm_timeout = llm_timeout or getattr(get_config().quality, "llm_mapping_timeout", 5) or 5
        self.similarity_threshold = similarity_threshold
        self._feedback_store: list[dict[str, Any]] = []
        self._embedding_model = None
        self.feedback_store = feedback_store or FeedbackStore()

    def _build_llm_config(self) -> Dict[str, Any]:
        return _build_llm_config_from_env(self.provider)

    def _token_similarity(self, left: str, right: str) -> float:
        left_tokens = Counter(re.findall(r"[a-z0-9]+", left.lower()))
        right_tokens = Counter(re.findall(r"[a-z0-9]+", right.lower()))
        if not left_tokens and not right_tokens:
            return 1.0
        if not left_tokens or not right_tokens:
            return 0.0
        overlap = sum((left_tokens & right_tokens).values())
        union = sum((left_tokens | right_tokens).values())
        return overlap / union if union else 0.0

    def _embedding_similarity(self, left: str, right: str) -> float:
        try:
            from sentence_transformers import SentenceTransformer
        except Exception:
            return self._token_similarity(left, right)

        if self._embedding_model is None:
            self._embedding_model = SentenceTransformer(
                "sentence-transformers/all-MiniLM-L6-v2"
            )
        try:
            embeddings = self._embedding_model.encode([left, right], normalize_embeddings=True)
            left_embedding = embeddings[0]
            right_embedding = embeddings[1]
            dot = float(left_embedding @ right_embedding)
            magnitude = max(float(left_embedding @ left_embedding) ** 0.5, 1e-9)
            other_magnitude = max(float(right_embedding @ right_embedding) ** 0.5, 1e-9)
            return dot / (magnitude * other_magnitude)
        except Exception:
            return self._token_similarity(left, right)

    def _find_similarity_mapping(self, step_text: str) -> Optional[MappingResult]:
        best_result: Optional[MappingResult] = None
        best_score = 0.0
        
        # First, try to find proven mappings from feedback store
        passing_results = self.feedback_store.get_passing_results(limit=200)
        for result in passing_results:
            known_text = result.step_text
            similarity = self._embedding_similarity(step_text, known_text)
            if similarity >= self.similarity_threshold and similarity > best_score:
                best_score = similarity
                # Build a MappingResult from the feedback record
                best_result = MappingResult(
                    action_type=ActionType[result.action_type],
                    selector=result.selector,
                    value=None,
                    options={},
                    confidence=round(best_score, 2),
                    source="similarity",
                    reason=f"Similar to proven mapping (similarity: {best_score:.2f})",
                    step_text=step_text,
                )
        
        # Fall back to in-memory feedback if no proven results found
        if best_result is None:
            for entry in self._feedback_store:
                known_text = str(entry.get("step_text", ""))
                similarity = self._embedding_similarity(step_text, known_text)
                if similarity >= self.similarity_threshold and similarity > best_score:
                    best_score = similarity
                    best_result = entry.get("mapping")
            if best_result is None:
                return None
            best_result.step_text = step_text
            best_result.confidence = max(best_result.confidence, round(best_score, 2))
            best_result.source = "similarity"
            best_result.reason = "Closest known feedback mapping"
        
        return best_result

    def record_feedback(
        self,
        step_text: str,
        mapping: MappingResult | Tuple[ActionType, Optional[str], Optional[str], Dict[str, Any]],
    ) -> None:
        if isinstance(mapping, MappingResult):
            result = mapping
        else:
            action_type, selector, value, options = mapping
            result = MappingResult(
                action_type=action_type,
                selector=selector,
                value=value,
                options=options or {},
                confidence=0.95,
                source="feedback",
                reason="manual correction",
                step_text=step_text,
            )
        self._feedback_store.append(
            {"step_text": step_text, "mapping": result}
        )

    async def _map_with_llm_async(self, step_text: str) -> MappingResult:
        key = _cache_key(step_text)
        if key in _CACHE:
            _LOGGER.debug("LLM cache hit for step: %s", key)
            mapping_tuple = _CACHE[key]
            action, target, value, options = mapping_tuple
            return MappingResult(
                action_type=action,
                selector=target,
                value=value,
                options=options,
                confidence=0.9,
                source="cache",
                reason="cached mapping",
                step_text=step_text,
            )

        quality = get_config().quality
        prompt = _build_prompt(step_text)
        llm_config = self._build_llm_config()
        timeout = self.llm_timeout if self.llm_timeout else quality.llm_mapping_timeout

        raw_output = None
        try:
            _LOGGER.debug("Calling LLM for step mapping: %s", step_text)
            raw_output = await asyncio.wait_for(
                _call_llm(prompt, llm_config), timeout=timeout
            )
            mapping = _parse_llm_output(raw_output, step_text)
        except asyncio.TimeoutError as exc:
            raise LLMTimeoutError(step_text, timeout) from exc
        except StepMappingError:
            raise
        except Exception as exc:
            _LOGGER.debug(
                "LLM mapping failed on first attempt for '%s': %s", step_text, exc
            )
            retry_prompt = (
                prompt
                + "\n\nIMPORTANT: Please respond with valid JSON only. The JSON object must include action, target, value, and options."
            )
            try:
                raw_output = await asyncio.wait_for(
                    _call_llm(retry_prompt, llm_config), timeout=timeout
                )
                mapping = _parse_llm_output(raw_output, step_text)
            except asyncio.TimeoutError as retry_exc:
                raise LLMTimeoutError(step_text, timeout) from retry_exc
            except StepMappingError:
                raise
            except Exception as retry_exc:
                raise StepMappingError(
                    step_text,
                    f"LLM mapping failed after retry: {retry_exc}",
                    ["Retry with a shorter, more explicit step description or increase llm_mapping_timeout."],
                ) from retry_exc

        if not isinstance(mapping, dict):
            raise StepMappingError(
                step_text,
                "LLM response must be a JSON object",
                ["Ensure the model returns a JSON object rather than free-form text."],
            )

        action = _normalize_action(
            mapping.get("action") or mapping.get("Action") or "",
            step_text,
        )
        target = mapping.get("target") if mapping.get("target") is not None else None
        value = mapping.get("value") if mapping.get("value") is not None else None
        options = mapping.get("options") or {}
        if not isinstance(options, dict):
            options = {}

        result = MappingResult(
            action_type=action,
            selector=target,
            value=value,
            options=options,
            confidence=0.88,
            source="llm",
            reason="LLM response",
            step_text=step_text,
        )
        _add_to_cache(key, (action, target, value, options))
        return result

    def _add_selector_alternatives(self, mapping_result: MappingResult) -> MappingResult:
        """Add selector candidate alternatives to a mapping result."""
        # Only generate alternatives for non-rule-engine sources to avoid redundancy
        if mapping_result.selector and mapping_result.source in ("llm", "similarity", "feedback"):
            candidates = SelectorGenerator.generate_alternatives(mapping_result.selector)
            if candidates:
                mapping_result.selector_candidates = candidates
        return mapping_result

    def map_step(
        self,
        step_text: str,
        use_llm: bool = True,
        fallback_to_rules: bool = True,
        fallback_engine: Optional[RuleEngine] = None,
        interactive_callback: Optional[
            Callable[[str, str, list[str]], Tuple[ActionType, Optional[str], Optional[str], Dict[str, Any]]]
        ] = None,
        prefer_rule_engine: bool = True,
    ) -> MappingResult:
        if not step_text:
            raise ValueError("Empty step text")

        if prefer_rule_engine:
            candidate_mappings = self.get_candidate_mappings(step_text)
            if candidate_mappings:
                first_candidate = candidate_mappings[0]
                action = ActionType[first_candidate["action"]]
                return MappingResult(
                    action_type=action,
                    selector=first_candidate.get("target"),
                    value=first_candidate.get("value"),
                    options=first_candidate.get("options") or {},
                    confidence=0.95,
                    source="rule_engine",
                    reason="regex rule matched",
                    step_text=step_text,
                )

        if not use_llm:
            raise ValueError(f"No rule matches step: {step_text}")

        try:
            result = asyncio.run(self._map_with_llm_async(step_text))
            return self._add_selector_alternatives(result)
        except Exception as exc:
            _LOGGER.debug("LLM mapping error for '%s': %s", step_text, exc)
            similarity_result = self._find_similarity_mapping(step_text)
            if similarity_result is not None:
                return self._add_selector_alternatives(similarity_result)
            if fallback_to_rules:
                try:
                    fallback_mapping = (fallback_engine or RuleEngine()).map_step(step_text)
                    return MappingResult(
                        action_type=fallback_mapping[0],
                        selector=fallback_mapping[1],
                        value=fallback_mapping[2],
                        options=fallback_mapping[3],
                        confidence=0.7,
                        source="rule_engine",
                        reason="fallback after LLM failure",
                        step_text=step_text,
                    )
                except ValueError as rules_exc:
                    if interactive_callback is not None:
                        mapped = interactive_callback(step_text, str(rules_exc), [])
                        return MappingResult(
                            action_type=mapped[0],
                            selector=mapped[1],
                            value=mapped[2],
                            options=mapped[3],
                            confidence=0.5,
                            source="interactive",
                            reason="manual correction",
                            step_text=step_text,
                        )
                    raise
            if interactive_callback is not None:
                mapped = interactive_callback(step_text, str(exc), [])
                return MappingResult(
                    action_type=mapped[0],
                    selector=mapped[1],
                    value=mapped[2],
                    options=mapped[3],
                    confidence=0.5,
                    source="interactive",
                    reason="manual correction",
                    step_text=step_text,
                )
            raise

    def record_result(
        self,
        step_text: str,
        selector: Optional[str],
        action_type: ActionType,
        test_result: str,
        execution_context: Optional[Dict[str, Any]] = None,
        mapping_source: str = "unknown",
        confidence: float = 0.0,
    ) -> None:
        """
        Record the outcome of a mapping decision for future learning.

        Args:
            step_text: Original step text
            selector: Selector used in the mapping
            action_type: Action type (e.g., CLICK, FILL)
            test_result: Test outcome ('pass', 'fail', 'skipped')
            execution_context: Optional metadata (browser, page, error_msg, etc.)
            mapping_source: Source of the mapping (rule_engine, llm, similarity, interactive)
            confidence: Confidence score of the mapping (0.0-1.0)
        """
        self.feedback_store.record_result(
            step_text=step_text,
            selector=selector or "unknown",
            action_type=action_type.name if hasattr(action_type, "name") else str(action_type),
            test_result=test_result,
            execution_context=execution_context,
            mapping_source=mapping_source,
            confidence=confidence,
        )
        _LOGGER.debug(
            f"Recorded {test_result} result for mapping: {step_text} -> {action_type.name if hasattr(action_type, 'name') else str(action_type)} {selector}"
        )

    def get_selector_success_rate(self, selector: Optional[str]) -> float:
        """
        Get the historical success rate for a selector.

        Args:
            selector: Selector string

        Returns:
            Success rate as float (0.0-1.0)
        """
        if not selector:
            return 0.0
        return self.feedback_store.get_success_rate(selector)




async def map_step_with_llm(
    step_text: str,
) -> Tuple[ActionType, Optional[str], Optional[str], Dict[str, Any]]:
    mapper = LLMStepMapper()
    result = await mapper._map_with_llm_async(step_text)
    return result.to_tuple()


def map_step(
    step_text: str,
    use_llm: bool = True,
    fallback_to_rules: bool = True,
    fallback_engine: Optional[RuleEngine] = None,
    interactive_callback: Optional[
        Callable[
            [str, str, list[str]],
            Tuple[ActionType, Optional[str], Optional[str], Dict[str, Any]],
        ]
    ] = None,
) -> Tuple[ActionType, Optional[str], Optional[str], Dict[str, Any]]:
    if not use_llm:
        return (fallback_engine or RuleEngine()).map_step(step_text)

    mapper = LLMStepMapper()
    key = _cache_key(step_text)
    if key in _CACHE:
        _LOGGER.debug("LLM cache hit for step: %s", key)
        return _CACHE[key]

    try:
        result = asyncio.run(mapper._map_with_llm_async(step_text))
        return result.to_tuple()
    except Exception as exc:
        _LOGGER.debug("LLM mapping error for '%s': %s", step_text, exc)
        similarity_result = mapper._find_similarity_mapping(step_text)
        if similarity_result is not None:
            return similarity_result.to_tuple()
        if fallback_to_rules:
            _LOGGER.debug("Falling back to RuleEngine for step: %s", step_text)
            try:
                return (fallback_engine or RuleEngine()).map_step(step_text)
            except ValueError as rules_exc:
                if interactive_callback is not None:
                    _LOGGER.debug(
                        "Invoking interactive callback for step: %s", step_text
                    )
                    return interactive_callback(step_text, str(rules_exc), [])
                raise
        if interactive_callback is not None:
            _LOGGER.debug(
                "Invoking interactive callback after LLM failure for step: %s",
                step_text,
            )
            return interactive_callback(step_text, str(exc), [])
        raise


# Load cache at import time so it is persistent across runs.
_load_persistent_cache()
