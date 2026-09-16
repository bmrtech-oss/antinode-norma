import re
from typing import List, Set
from antinode_norma.gates.types import BaseGate, GateContext
from antinode_norma.core.types import GateResult

# Recognized general category/utility tags that aren't test-case ID tags
KNOWN_SYSTEM_TAGS = {
    "smoke",
    "regression",
    "slow",
    "fast",
    "api",
    "ui",
    "unit",
    "integration",
    "wip",
    "ignore",
    "skip",
    "manual",
    "automated",
    "critical",
    "high",
    "medium",
    "low",
}


def _extract_gherkin_tags(gherkin_text: str) -> Set[str]:
    """Extract all tag names without the leading '@', avoiding email false positives."""
    raw_tags = re.findall(r"(?:^|\s)@([\w\-]+)", gherkin_text)
    return set(raw_tags)


def _normalize_id(id_str: str) -> str:
    """Strip leading @ if present and lower-case for comparison."""
    return id_str.lstrip("@").strip().lower()


class Q3TraceabilityGate(BaseGate):
    """
    Quality Gate Q3: Every TestCase.id appears as a @-tag in the Gherkin text.
    """

    gate_id: str = "Q3"
    is_hard_gate: bool = True

    def evaluate(self, context: GateContext) -> GateResult:
        if not context.test_cases:
            return GateResult(
                gate_id=self.gate_id,
                passed=True,
                score=1.0,
                issues=[],
                suggestions=[],
            )

        gherkin_tags = {_normalize_id(t) for t in _extract_gherkin_tags(context.gherkin_text)}
        missing_ids: List[str] = []

        for tc in context.test_cases:
            tc_norm_id = _normalize_id(tc.id)
            # Check if normalized ID is present directly as tag or in gherkin tags
            if tc_norm_id not in gherkin_tags:
                missing_ids.append(tc.id)

        if not missing_ids:
            return GateResult(
                gate_id=self.gate_id,
                passed=True,
                score=1.0,
                issues=[],
                suggestions=[],
            )

        missing_str = ", ".join(missing_ids)
        return GateResult(
            gate_id=self.gate_id,
            passed=False,
            score=0.0,
            issues=[f"TestCase ID(s) missing from Gherkin tags: {missing_str}"],
            suggestions=["Add corresponding @<test_case_id> tags to the feature or scenarios."],
        )


class Q4OrphanTagsGate(BaseGate):
    """
    Quality Gate Q4: No orphan tags.
    Every ID-like tag in Gherkin text must map back to a known TestCase.id or system tag.
    """

    gate_id: str = "Q4"
    is_hard_gate: bool = True

    def evaluate(self, context: GateContext) -> GateResult:
        gherkin_tags = _extract_gherkin_tags(context.gherkin_text)
        known_ids = {_normalize_id(tc.id) for tc in context.test_cases}

        # Also collect any tags listed directly inside test_cases.tags
        for tc in context.test_cases:
            for tag in tc.tags:
                known_ids.add(_normalize_id(tag))

        orphan_tags: List[str] = []

        for tag in gherkin_tags:
            norm_tag = _normalize_id(tag)
            # If it's a known system tag, skip
            if norm_tag in KNOWN_SYSTEM_TAGS:
                continue
            # If it matches a known test case ID or explicit test case tag, skip
            if norm_tag in known_ids:
                continue
            # Otherwise it's an orphan tag
            orphan_tags.append(f"@{tag}")

        if not orphan_tags:
            return GateResult(
                gate_id=self.gate_id,
                passed=True,
                score=1.0,
                issues=[],
                suggestions=[],
            )

        orphans_str = ", ".join(sorted(orphan_tags))
        return GateResult(
            gate_id=self.gate_id,
            passed=False,
            score=0.0,
            issues=[f"Orphan tag(s) detected: {orphans_str}"],
            suggestions=["Remove unused tags or associate them with known TestCase IDs."],
        )
