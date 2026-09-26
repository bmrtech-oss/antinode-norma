from typing import List, Optional
from antinode_norma.gates.types import BaseGate, GateContext
from antinode_norma.gates.graph import Q11GraphConsistencyGate, Q12GraphCoverageGate
from antinode_norma.core.features import FeatureFlagResolver
from antinode_norma.core.types import Verdict, GateResult
from antinode_norma.gates.aggregate import aggregate_results
from antinode_norma.gates.norma_validator import Q0NormaValidatorGate
from antinode_norma.gates.syntax import Q1SyntaxGate
from antinode_norma.gates.rspec_guard import Q2RSpecGuardGate
from antinode_norma.gates.traceability import Q3TraceabilityGate, Q4OrphanTagsGate
from antinode_norma.gates.duplicates import Q5DuplicatesGate
from antinode_norma.gates.declarative import Q6DeclarativeStyleGate
from antinode_norma.gates.reuse import Q7StepReuseGate
from antinode_norma.gates.outline import Q8OutlineUsageGate
from antinode_norma.gates.state import Q9StateModelGate
from antinode_norma.gates.semantic import Q10SemanticJudgeGate


class GateRunner:
    """
    Quality Gate Runner.
    Runs configured quality gates against a GateContext and aggregates results into a Verdict.
    Default gate configuration includes hard gates Q0-Q5 and soft gates Q6-Q10.
    """

    def __init__(self, gates: Optional[List[BaseGate]] = None):
        if gates is None:
            self.gates: List[BaseGate] = [
                Q0NormaValidatorGate(),
                Q1SyntaxGate(),
                Q2RSpecGuardGate(),
                Q3TraceabilityGate(),
                Q4OrphanTagsGate(),
                Q5DuplicatesGate(),
                Q6DeclarativeStyleGate(),
                Q7StepReuseGate(),
                Q8OutlineUsageGate(),
                Q9StateModelGate(),
                Q10SemanticJudgeGate(),
            ]
            if FeatureFlagResolver().is_enabled("knowledge_graph"):
                self.gates.append(Q11GraphConsistencyGate())
                self.gates.append(Q12GraphCoverageGate())
        else:
            self.gates = gates

    def evaluate(self, context: GateContext) -> Verdict:
        """Run all gates against the context and aggregate the results into a Verdict."""
        results: List[GateResult] = []
        hard_gate_ids = {}

        for gate in self.gates:
            res = gate.evaluate(context)
            results.append(res)
            hard_gate_ids[gate.gate_id] = gate.is_hard_gate

        return aggregate_results(results, hard_gate_ids=hard_gate_ids)

    def generate_report(self, verdict: Verdict) -> str:
        """Generate a human-readable Markdown validation report from a Verdict."""
        lines = [
            "# Quality Gate Validation Report",
            "",
            f"**Overall Summary:** {verdict.summary}",
            f"**Hard Gates Passed:** {'Yes' if verdict.hard_pass else 'No'}",
            f"**Soft Score:** {verdict.soft_score:.2f}",
            f"**Semantic Score:** {verdict.sem_score:.2f}",
            "",
            "## Individual Gate Outcomes",
            "",
        ]

        for gate_id, res in sorted(verdict.gate_results.items()):
            status = "PASSED" if res.passed else "FAILED"
            lines.append(f"### Gate {gate_id} — {status}")
            lines.append(f"- **Score:** {res.score:.2f}")

            if res.issues:
                lines.append("- **Issues:**")
                for issue in res.issues:
                    lines.append(f"  - {issue}")

            if res.suggestions:
                lines.append("- **Suggestions:**")
                for suggestion in res.suggestions:
                    lines.append(f"  - {suggestion}")

            lines.append("")

        return "\n".join(lines)
