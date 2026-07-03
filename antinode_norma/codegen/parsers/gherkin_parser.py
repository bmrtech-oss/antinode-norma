"""
Gherkin parser implementation using behave (stable and widely used).
"""

from pathlib import Path
from typing import Callable, List, Optional

from behave.parser import parse_feature
from behave.model import Feature, Step

from .base import Parser
from ..models.test_model import TestSuite, TestCase, TestStep
from ..engine.rules import RuleEngine
from ..engine.llm_step_mapper import map_step as map_step_with_llm, LLMStepMapper
from ..engine.prompt_library import Domain
from ..engine.exceptions import StepMappingError, LLMTimeoutError, SelectorNotFoundError
from ..config import get_config


def _normalize_domain(domain_name: Optional[str]) -> Optional[Domain]:
    if not domain_name:
        return None
    if isinstance(domain_name, Domain):
        return domain_name
    try:
        return Domain(domain_name.strip().lower())
    except Exception:
        return None


class GherkinParser(Parser):
    """Parse .feature files using behave (stable and widely used)."""

    def __init__(
        self,
        rule_engine: Optional[RuleEngine] = None,
        quality_config=None,
        interactive_callback: Optional[Callable[[str, str, list[str]], tuple]] = None,
        mapping_decisions: Optional[list[dict]] = None,
        mapping_decisions_log_path: Optional[Path] = None,
        use_richer_mapper: bool = False,
    ):
        self.rule_engine = rule_engine or RuleEngine()
        self.quality = quality_config or get_config().quality
        self.interactive_callback = interactive_callback
        self.mapping_decisions = mapping_decisions if mapping_decisions is not None else []
        self.mapping_decisions_log_path = mapping_decisions_log_path
        self.use_richer_mapper = use_richer_mapper
        if use_richer_mapper:
            cfg = get_config()
            mapper_domain = _normalize_domain(getattr(cfg, "domain", None))
            mapper_prompt_version = getattr(cfg, "prompt_version", "latest") or "latest"
            self.mapper = LLMStepMapper(
                domain=mapper_domain,
                prompt_version=mapper_prompt_version,
            )
        else:
            self.mapper = None

    def parse(self, source: Path) -> TestSuite:
        """
        Parse a .feature file and return a TestSuite.
        """
        try:
            # Read the file content as string
            content = source.read_text(encoding="utf-8")
        except Exception as e:
            raise ValueError(f"Failed to read file {source}: {e}")

        try:
            # behave's parse_feature expects the feature text string, not the path
            feature: Feature = parse_feature(content)
        except Exception as e:
            raise ValueError(f"Failed to parse {source} with behave: {e}")

        suite = self._feature_to_testsuite(feature)
        if self.mapping_decisions_log_path is not None:
            self._write_mapping_decisions_log()
        return suite

    def _feature_to_testsuite(self, feature: Feature) -> TestSuite:
        """Convert a behave Feature to our TestSuite."""
        background_steps: List[TestStep] = []
        if feature.background:
            background_steps = self._behave_steps_to_teststeps(feature.background.steps)

        cases = []
        for scenario in feature.scenarios:
            steps = background_steps.copy() + self._behave_steps_to_teststeps(
                scenario.steps
            )
            cases.append(
                TestCase(
                    name=scenario.name or "Untitled Scenario",
                    steps=steps,
                    tags=[self._tag_text(tag) for tag in scenario.tags],
                    description=scenario.description or "",
                    background=background_steps if feature.background else None,
                )
            )

        return TestSuite(
            name=feature.name or "Untitled Feature",
            cases=cases,
            description=feature.description or "",
            tags=[self._tag_text(tag) for tag in feature.tags],
            background=background_steps if feature.background else None,
        )

    def _tag_text(self, tag) -> str:
        """Return the tag name text for behave Tag objects."""
        return getattr(tag, "name", getattr(tag, "text", str(tag)))

    def _write_mapping_decisions_log(self) -> None:
        if not self.mapping_decisions_log_path:
            return
        self.mapping_decisions_log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.mapping_decisions_log_path.open("w", encoding="utf-8") as handle:
            for decision in self.mapping_decisions:
                handle.write(__import__("json").dumps(decision, sort_keys=True) + "\n")

    def _behave_steps_to_teststeps(self, behave_steps: List[Step]) -> List[TestStep]:
        """Convert behave Step objects to our TestStep model."""
        result = []
        for step in behave_steps:
            keyword = step.keyword.strip()
            text = step.name
            step_text = f"{keyword} {text}".strip()
            candidate_mappings = self.rule_engine.get_candidate_mappings(step_text)
            decision = {
                "input_text": step_text,
                "candidate_mappings": candidate_mappings,
                "selected_mapping": None,
                "confidence": 0.0,
                "reason": "No rule matched",
                "source": "unknown",
            }
            try:
                if self.use_richer_mapper and self.mapper:
                    mapping_result = self.mapper.map_step(
                        step_text,
                        use_llm=self.quality.use_llm_mapping,
                        fallback_to_rules=True,
                        prefer_rule_engine=True,
                    )
                    action = mapping_result.action_type
                    target = mapping_result.selector
                    value = mapping_result.value
                    options = mapping_result.options or {}
                    decision["selected_mapping"] = {
                        "action": action.name if hasattr(action, "name") else str(action),
                        "target": target,
                        "value": value,
                        "options": options,
                    }
                    decision["confidence"] = mapping_result.confidence
                    decision["source"] = mapping_result.source
                    decision["reason"] = mapping_result.reason or "Mapping applied"
                else:
                    action, target, value, options = map_step_with_llm(
                        step_text,
                        use_llm=self.quality.use_llm_mapping,
                        fallback_to_rules=True,
                        fallback_engine=self.rule_engine,
                        interactive_callback=self.interactive_callback,
                    )
                    decision["selected_mapping"] = {
                        "action": action.name if hasattr(action, "name") else str(action),
                        "target": target,
                        "value": value,
                        "options": options,
                    }
                    decision["confidence"] = 0.9 if candidate_mappings else 0.8
                    decision["source"] = "rule_engine" if candidate_mappings else "llm"
                    decision["reason"] = (
                        "Selected via rule-engine or LLM mapping"
                        if candidate_mappings
                        else "Selected via LLM mapping"
                    )
            except (StepMappingError, LLMTimeoutError, SelectorNotFoundError) as exc:
                decision["reason"] = f"Mapping failed: {exc}"
                decision["confidence"] = 0.0
                decision["source"] = "error"
                raise ValueError(f"Unmapped step: '{step_text}'. {exc}") from exc
            except ValueError as exc:
                decision["reason"] = f"Mapping failed: {exc}"
                decision["confidence"] = 0.0
                decision["source"] = "error"
                raise ValueError(f"Unmapped step: '{step_text}'. {exc}") from exc

            if self.mapping_decisions is not None:
                self.mapping_decisions.append(decision)

            result.append(
                TestStep(
                    action=action,
                    target=target,
                    value=value,
                    description=step_text,
                    options=options,
                )
            )
        return result
