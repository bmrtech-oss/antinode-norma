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
from ..engine.llm_step_mapper import map_step as map_step_with_llm
from ..config import get_config


class GherkinParser(Parser):
    """Parse .feature files using behave (stable and widely used)."""

    def __init__(
        self,
        rule_engine: Optional[RuleEngine] = None,
        quality_config=None,
        interactive_callback: Optional[Callable[[str, str, list[str]], tuple]] = None,
    ):
        self.rule_engine = rule_engine or RuleEngine()
        self.quality = quality_config or get_config().quality
        self.interactive_callback = interactive_callback

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

        return self._feature_to_testsuite(feature)

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

    def _behave_steps_to_teststeps(self, behave_steps: List[Step]) -> List[TestStep]:
        """Convert behave Step objects to our TestStep model."""
        result = []
        for step in behave_steps:
            keyword = step.keyword.strip()
            text = step.name
            step_text = f"{keyword} {text}".strip()
            try:
                action, target, value, options = map_step_with_llm(
                    step_text,
                    use_llm=self.quality.use_llm_mapping,
                    fallback_to_rules=True,
                    fallback_engine=self.rule_engine,
                    interactive_callback=self.interactive_callback,
                )
            except ValueError as e:
                raise ValueError(f"Unmapped step: '{step_text}'. {e}")
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
