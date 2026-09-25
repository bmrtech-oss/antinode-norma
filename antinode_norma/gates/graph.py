from typing import Optional

from antinode_norma.core.types import GateResult
from antinode_norma.gates.types import BaseGate, GateContext
from antinode_norma.knowledge_graph import KnowledgeGraphStore


class Q11GraphConsistencyGate(BaseGate):
    """Quality Gate Q11: reject facts that contradict the curated graph."""

    gate_id: str = "Q11"
    is_hard_gate: bool = True

    def __init__(self, store: Optional[KnowledgeGraphStore] = None):
        self.store = store or KnowledgeGraphStore()

    def evaluate(self, context: GateContext) -> GateResult:
        contradictions = self.store.find_contradictions(context.gherkin_text)
        if not contradictions:
            return GateResult(
                gate_id=self.gate_id,
                passed=True,
                score=1.0,
                issues=[],
                suggestions=[],
            )

        ids = ", ".join(fact["id"] for fact in contradictions)
        return GateResult(
            gate_id=self.gate_id,
            passed=False,
            score=0.0,
            issues=[f"Knowledge-graph contradiction(s) detected: {ids}"],
            suggestions=["Revise the scenario so it does not contradict curated domain facts."],
        )


class Q12GraphCoverageGate(BaseGate):
    """Quality Gate Q12: require curated graph concepts in generated text."""

    gate_id: str = "Q12"
    is_hard_gate: bool = True

    def __init__(self, store: Optional[KnowledgeGraphStore] = None, minimum_matches: int = 1):
        self.store = store or KnowledgeGraphStore()
        self.minimum_matches = minimum_matches

    def evaluate(self, context: GateContext) -> GateResult:
        text = context.gherkin_text.lower()
        matched = [
            fact["id"]
            for fact in self.store.facts()
            if fact["subject"].lower() in text or fact["object"].lower() in text
        ]
        if len(matched) >= self.minimum_matches:
            return GateResult(gate_id=self.gate_id, passed=True, score=1.0, issues=[], suggestions=[])
        return GateResult(
            gate_id=self.gate_id,
            passed=False,
            score=0.0,
            issues=["Generated text does not reference enough curated graph concepts."],
            suggestions=["Include relevant domain entities or values represented in the curated graph."],
        )
