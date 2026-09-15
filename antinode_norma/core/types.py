from typing import List, Dict, Any
from pydantic import BaseModel, Field


class TestCase(BaseModel):
    id: str
    title: str
    role: str = "user"
    action: str = ""
    benefit: str = ""
    acceptance_criteria: List[str] = Field(default_factory=list)
    steps: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DomainEntity(BaseModel):
    name: str
    attributes: List[str] = Field(default_factory=list)
    relationships: Dict[str, str] = Field(default_factory=dict)


class DomainModel(BaseModel):
    name: str = "default"
    entities: List[DomainEntity] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GateResult(BaseModel):
    gate_id: str
    passed: bool
    score: float = 1.0
    issues: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)


class Verdict(BaseModel):
    hard_pass: bool
    soft_score: float = 0.0
    sem_score: float = 0.0
    gate_results: Dict[str, GateResult] = Field(default_factory=dict)
    summary: str = ""

    @property
    def is_overall_pass(self) -> bool:
        return self.hard_pass and self.soft_score >= 0.85 and self.sem_score >= 0.85
