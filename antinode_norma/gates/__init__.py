"""Quality gates package for Norma BDD platform."""

from antinode_norma.gates.types import BaseGate, GateContext
from antinode_norma.gates.aggregate import aggregate_results
from antinode_norma.gates.norma_validator import Q0NormaValidatorGate
from antinode_norma.gates.syntax import Q1SyntaxGate
from antinode_norma.gates.rspec_guard import Q2RSpecGuardGate

__all__ = [
    "BaseGate",
    "GateContext",
    "aggregate_results",
    "Q0NormaValidatorGate",
    "Q1SyntaxGate",
    "Q2RSpecGuardGate",
]
