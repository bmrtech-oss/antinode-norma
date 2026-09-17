import re
from typing import List, Dict
from antinode_norma.gates.types import BaseGate, GateContext
from antinode_norma.core.types import GateResult

STEP_KEYWORDS = ("Given", "When", "Then", "And", "But")


def _normalize_step(step_text: str) -> str:
    """Normalize a step by removing keyword, lowercasing, and replacing parameters."""
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


class Q7StepReuseGate(BaseGate):
    """
    Quality Gate Q7: Step reuse check (Soft Gate).
    Evaluates the reuse of step definitions/phrases across scenarios.
    Threshold: score >= 0.90
    """

    gate_id: str = "Q7"
    is_hard_gate: bool = False

    def evaluate(self, context: GateContext) -> GateResult:
        steps: List[str] = []
        scenario_count = 0

        if context.gherkin_text:
            lines = context.gherkin_text.splitlines()
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("Scenario:") or stripped.startswith("Scenario Outline:"):
                    scenario_count += 1
                for kw in STEP_KEYWORDS:
                    if stripped.startswith(f"{kw} "):
                        steps.append(stripped)
                        break
        elif context.test_cases:
            scenario_count = len(context.test_cases)
            for tc in context.test_cases:
                steps.extend(tc.steps)

        if not steps:
            return GateResult(
                gate_id=self.gate_id,
                passed=True,
                score=1.0,
                issues=[],
                suggestions=[],
            )

        normalized_steps = [_normalize_step(s) for s in steps]
        counts: Dict[str, int] = {}
        for ns in normalized_steps:
            counts[ns] = counts.get(ns, 0) + 1

        total_steps = len(normalized_steps)

        if scenario_count <= 1:
            reused_steps = sum(c for c in counts.values() if c >= 2)
            if reused_steps == 0:
                return GateResult(
                    gate_id=self.gate_id,
                    passed=True,
                    score=1.0,
                    issues=[],
                    suggestions=["Add more scenarios to evaluate vocabulary reuse across scenarios."],
                )

        reused_steps = sum(c for c in counts.values() if c >= 2)
        score = reused_steps / total_steps
        passed = score >= 0.90

        issues = []
        suggestions = []
        if not passed:
            unique_steps = [s for s, c in counts.items() if c == 1]
            issues = [f"Step phrase used only once: '{s}'" for s in unique_steps[:5]]
            suggestions = ["Reuse existing step vocabulary across scenarios to improve test maintainability."]

        return GateResult(
            gate_id=self.gate_id,
            passed=passed,
            score=round(score, 4),
            issues=issues,
            suggestions=suggestions,
        )
