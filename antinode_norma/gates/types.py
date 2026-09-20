from abc import ABC, abstractmethod
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
from antinode_norma.core.types import TestCase, DomainModel, GateResult


class GateContext(BaseModel):
    gherkin_text: str = ""
    test_cases: List[TestCase] = Field(default_factory=list)
    domain_model: Optional[DomainModel] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseGate(ABC):
    gate_id: str
    is_hard_gate: bool = True

    @abstractmethod
    def evaluate(self, context: GateContext) -> GateResult:
        """Evaluate the quality gate against the provided GateContext."""
        pass
