import re
from typing import List
from antinode_norma.gates.types import BaseGate, GateContext
from antinode_norma.core.types import GateResult

FORBIDDEN_RSPEC_TOKENS = [
    "describe",
    "context",
    "expect",
    "should",
    "let",
    "before",
    "after",
]


class Q2RSpecGuardGate(BaseGate):
    """
    Quality Gate Q2: No RSpec tokens guard.
    Checks for presence of RSpec/unit-test keywords in Gherkin text.
    Forbidden keywords: describe, context, expect, should, let, before, after.
    """

    gate_id: str = "Q2"
    is_hard_gate: bool = True

    def evaluate(self, context: GateContext) -> GateResult:
        text = context.gherkin_text
        found_tokens: List[str] = []

        for token in FORBIDDEN_RSPEC_TOKENS:
            pattern = rf"\b{re.escape(token)}\b"
            if re.search(pattern, text, re.IGNORECASE):
                found_tokens.append(token)

        if not found_tokens:
            return GateResult(
                gate_id=self.gate_id,
                passed=True,
                score=1.0,
                issues=[],
                suggestions=[],
            )

        tokens_str = ", ".join(sorted(found_tokens))
        return GateResult(
            gate_id=self.gate_id,
            passed=False,
            score=0.0,
            issues=[f"Forbidden RSpec keyword(s) detected: {tokens_str}"],
            suggestions=["Remove RSpec/unit-testing vocabulary from Gherkin feature files."],
        )
