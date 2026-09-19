from antinode_norma.gates.types import BaseGate, GateContext
from antinode_norma.core.types import GateResult
from antinode_norma.core.validator import validate_gherkin


class Q0NormaValidatorGate(BaseGate):
    """Gate Q0: Norma Gherkin validator pass check."""

    gate_id: str = "Q0"
    is_hard_gate: bool = True

    def evaluate(self, context: GateContext) -> GateResult:
        if not context.gherkin_text or not context.gherkin_text.strip():
            return GateResult(
                gate_id=self.gate_id,
                passed=False,
                score=0.0,
                issues=["Gherkin feature text is empty"],
                suggestions=["Provide valid Gherkin feature content."],
            )

        validation = validate_gherkin(context.gherkin_text)
        passed = validation.valid
        issues = validation.errors if not passed else []
        suggestions = ["Fix Gherkin syntax or structural errors in feature file."] if not passed else []

        return GateResult(
            gate_id=self.gate_id,
            passed=passed,
            score=1.0 if passed else 0.0,
            issues=issues,
            suggestions=suggestions,
        )
