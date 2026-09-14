from typing import List, Set
from antinode_norma.gates.types import BaseGate, GateContext
from antinode_norma.core.types import GateResult

STEP_KEYWORDS = ("Given", "When", "Then", "And", "But")


def _get_step_keyword(line: str) -> str:
    """Extract keyword from a step line."""
    stripped = line.strip()
    for kw in STEP_KEYWORDS:
        if stripped.startswith(f"{kw} "):
            return kw
    return ""


def _evaluate_gherkin_state_keywords(gherkin_text: str) -> List[dict]:
    """Parse Gherkin text and return status for each scenario."""
    lines = gherkin_text.splitlines()
    has_background_given = False
    in_background = False

    scenarios = []
    current_scenario_title = ""
    current_keywords: Set[str] = set()
    in_scenario = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("Background:"):
            in_background = True
            in_scenario = False
        elif stripped.startswith("Scenario:") or stripped.startswith("Scenario Outline:"):
            if in_scenario and current_scenario_title:
                scenarios.append({
                    "title": current_scenario_title,
                    "keywords": current_keywords.copy(),
                })
            in_background = False
            in_scenario = True
            current_scenario_title = stripped
            current_keywords = set()
        elif in_background:
            kw = _get_step_keyword(stripped)
            if kw == "Given":
                has_background_given = True
        elif in_scenario:
            kw = _get_step_keyword(stripped)
            if kw in ("Given", "When", "Then"):
                current_keywords.add(kw)

    if in_scenario and current_scenario_title:
        scenarios.append({
            "title": current_scenario_title,
            "keywords": current_keywords.copy(),
        })

    results = []
    for sc in scenarios:
        kws = sc["keywords"]
        has_given = ("Given" in kws) or has_background_given
        has_when = "When" in kws
        has_then = "Then" in kws
        compliant = has_given and has_when and has_then
        results.append({
            "title": sc["title"],
            "compliant": compliant,
            "missing": [kw for kw, present in [("Given", has_given), ("When", has_when), ("Then", has_then)] if not present],
        })

    return results


class Q9StateModelGate(BaseGate):
    """
    Quality Gate Q9: State Keywords check (Soft Gate).
    Evaluates whether scenarios contain Given, When, and Then state transition keywords.
    Threshold: score == 1.00
    """

    gate_id: str = "Q9"
    is_hard_gate: bool = False

    def evaluate(self, context: GateContext) -> GateResult:
        scenario_evals = []

        if context.gherkin_text:
            scenario_evals = _evaluate_gherkin_state_keywords(context.gherkin_text)
        elif context.test_cases:
            for tc in context.test_cases:
                kws = set()
                for step in tc.steps:
                    kw = _get_step_keyword(step)
                    if kw in ("Given", "When", "Then"):
                        kws.add(kw)
                has_given = "Given" in kws
                has_when = "When" in kws
                has_then = "Then" in kws
                scenario_evals.append({
                    "title": tc.title or tc.id,
                    "compliant": has_given and has_when and has_then,
                    "missing": [kw for kw, present in [("Given", has_given), ("When", has_when), ("Then", has_then)] if not present],
                })

        if not scenario_evals:
            return GateResult(
                gate_id=self.gate_id,
                passed=True,
                score=1.0,
                issues=[],
                suggestions=[],
            )

        compliant_count = sum(1 for sc in scenario_evals if sc["compliant"])
        total_scenarios = len(scenario_evals)
        score = compliant_count / total_scenarios if total_scenarios > 0 else 1.0
        passed = score == 1.0

        issues = []
        suggestions = []
        if not passed:
            non_compliant = [sc for sc in scenario_evals if not sc["compliant"]]
            issues = [f"Scenario '{sc['title']}' missing keywords: {', '.join(sc['missing'])}" for sc in non_compliant[:5]]
            suggestions = ["Ensure all scenarios include Given (precondition), When (action), and Then (expected outcome) steps."]

        return GateResult(
            gate_id=self.gate_id,
            passed=passed,
            score=round(score, 4),
            issues=issues,
            suggestions=suggestions,
        )
