import re
from typing import List, Dict
from antinode_norma.gates.types import BaseGate, GateContext
from antinode_norma.core.types import GateResult

STEP_KEYWORDS = ("Given", "When", "Then", "And", "But")


def _normalize_step_structure(step_text: str) -> str:
    """Normalize a step by replacing quoted strings and numbers with placeholders."""
    stripped = step_text.strip()
    for kw in STEP_KEYWORDS:
        if stripped.startswith(f"{kw} "):
            stripped = stripped[len(kw) + 1 :].strip()
            break

    # Replace quoted strings with <param>
    normalized = re.sub(r'("[^"]*"|\'[^\']*\')', "<param>", stripped)
    # Replace numbers with <param>
    normalized = re.sub(r"\b\d+\b", "<param>", normalized)
    return normalized.lower()


def _extract_scenario_step_structures(gherkin_text: str) -> List[List[str]]:
    """Extract step structure sequences for each scenario in Gherkin text."""
    scenarios: List[List[str]] = []
    current_steps: List[str] = []
    in_scenario = False

    for line in gherkin_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("Scenario Outline:") or stripped.startswith("Scenario:"):
            if in_scenario and current_steps:
                scenarios.append(current_steps)
                current_steps = []
            # Scenario Outlines explicitly use outlines, so skip tracking them as candidate duplicates
            in_scenario = stripped.startswith("Scenario:")
        elif in_scenario:
            for kw in STEP_KEYWORDS:
                if stripped.startswith(f"{kw} "):
                    current_steps.append(_normalize_step_structure(stripped))
                    break

    if in_scenario and current_steps:
        scenarios.append(current_steps)

    return scenarios


class Q8OutlineUsageGate(BaseGate):
    """
    Quality Gate Q8: Scenario Outline Usage check (Soft Gate).
    Evaluates Gherkin scenarios to ensure combinatorial cases use Scenario Outline.
    Threshold: score == 1.00
    """

    gate_id: str = "Q8"
    is_hard_gate: bool = False

    def evaluate(self, context: GateContext) -> GateResult:
        scenario_structures: List[List[str]] = []

        if context.gherkin_text:
            scenario_structures = _extract_scenario_step_structures(context.gherkin_text)
        elif context.test_cases:
            for tc in context.test_cases:
                normalized = [_normalize_step_structure(s) for s in tc.steps]
                if normalized:
                    scenario_structures.append(normalized)

        if len(scenario_structures) <= 1:
            return GateResult(
                gate_id=self.gate_id,
                passed=True,
                score=1.0,
                issues=[],
                suggestions=[],
            )

        # Count occurrences of identical step structure sequences across Scenario blocks
        structure_counts: Dict[tuple, int] = {}
        for struct in scenario_structures:
            key = tuple(struct)
            structure_counts[key] = structure_counts.get(key, 0) + 1

        unoutlined_combinatorial_count = sum(c for c in structure_counts.values() if c >= 2)
        total_scenarios = len(scenario_structures)

        if unoutlined_combinatorial_count > 0:
            score = max(0.0, 1.0 - (unoutlined_combinatorial_count / total_scenarios))
            passed = score == 1.0
            issues = [
                f"Detected {unoutlined_combinatorial_count} repetitive Scenario blocks with identical step structures that should use Scenario Outline."
            ]
            suggestions = ["Refactor repetitive scenarios differing only by data parameters into a Scenario Outline with an Examples table."]
        else:
            score = 1.0
            passed = True
            issues = []
            suggestions = []

        return GateResult(
            gate_id=self.gate_id,
            passed=passed,
            score=round(score, 4),
            issues=issues,
            suggestions=suggestions,
        )
