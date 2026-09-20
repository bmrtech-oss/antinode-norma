import re
from typing import List
from antinode_norma.gates.types import BaseGate, GateContext
from antinode_norma.core.types import GateResult

# Patterns identifying low-level imperative UI actions instead of intent-level behavior
IMPERATIVE_PATTERNS = [
    r"\bclick\s+(on\s+)?(the\s+)?[\"'].*?[\"']\s+button\b",
    r"\btype\s+[\"'].*?[\"']\s+into\b",
    r"\bfill\s+in\s+(the\s+)?[\"'].*?[\"']\s+field\b",
    r"\bpress\s+(the\s+)?[\"'].*?[\"']\s+key\b",
    r"\bscroll\s+(down|up)\s+to\b",
    r"\bselect\s+[\"'].*?[\"']\s+from\s+(the\s+)?dropdown\b",
]

STEP_KEYWORDS = ("Given", "When", "Then", "And", "But")


class Q6DeclarativeStyleGate(BaseGate):
    """
    Quality Gate Q6: Declarative style check (Soft Gate).
    Evaluates Gherkin steps to ensure intent-level behavior rather than imperative UI mechanics.
    Threshold: score >= 0.90
    """

    gate_id: str = "Q6"
    is_hard_gate: bool = False

    def evaluate(self, context: GateContext) -> GateResult:
        lines = context.gherkin_text.splitlines()
        steps: List[str] = []

        for line in lines:
            stripped = line.strip()
            for kw in STEP_KEYWORDS:
                if stripped.startswith(f"{kw} "):
                    steps.append(stripped)
                    break

        if not steps:
            return GateResult(
                gate_id=self.gate_id,
                passed=True,
                score=1.0,
                issues=[],
                suggestions=[],
            )

        imperative_count = 0
        imperative_steps = []

        for step in steps:
            step_lower = step.lower()
            for pattern in IMPERATIVE_PATTERNS:
                if re.search(pattern, step_lower):
                    imperative_count += 1
                    imperative_steps.append(step)
                    break

        score = max(0.0, 1.0 - (imperative_count / len(steps)))
        passed = score >= 0.90

        issues = []
        suggestions = []
        if not passed:
            issues = [f"Imperative UI step detected: '{s}'" for s in imperative_steps]
            suggestions = ["Refactor imperative UI interactions into intent-based declarative steps."]

        return GateResult(
            gate_id=self.gate_id,
            passed=passed,
            score=score,
            issues=issues,
            suggestions=suggestions,
        )
