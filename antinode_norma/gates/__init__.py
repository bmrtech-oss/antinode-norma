"""Quality gates package for Norma BDD platform."""

from antinode_norma.gates.types import BaseGate, GateContext
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
from antinode_norma.gates.runner import GateRunner

__all__ = [
    "BaseGate",
    "GateContext",
    "aggregate_results",
    "Q0NormaValidatorGate",
    "Q1SyntaxGate",
    "Q2RSpecGuardGate",
    "Q3TraceabilityGate",
    "Q4OrphanTagsGate",
    "Q5DuplicatesGate",
    "Q6DeclarativeStyleGate",
    "Q7StepReuseGate",
    "Q8OutlineUsageGate",
    "Q9StateModelGate",
    "Q10SemanticJudgeGate",
    "GateRunner",
]
