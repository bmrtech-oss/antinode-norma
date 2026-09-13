from antinode_norma.gates.types import BaseGate, GateContext
from antinode_norma.core.types import GateResult
from antinode_norma.core.validator import validate_gherkin


class Q1SyntaxGate(BaseGate):
    """
    Quality Gate Q1: Valid Gherkin syntax check.
    Uses core validate_gherkin parser to check structure.
    """

    gate_id: str = "Q1"
    is_hard_gate: bool = True

    def evaluate(self, context: GateContext) -> GateResult:
        res = validate_gherkin(context.gherkin_text)
        if res.valid:
            return GateResult(
                gate_id=self.gate_id,
                passed=True,
                score=1.0,
                issues=[],
                suggestions=[],
            )
        else:
            return GateResult(
                gate_id=self.gate_id,
                passed=False,
                score=0.0,
                issues=res.errors,
                suggestions=["Ensure Feature, Scenario/Scenario Outline, and complete step keywords are used."],
            )
