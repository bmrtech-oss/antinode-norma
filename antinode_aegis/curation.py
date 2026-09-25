"""A2 knowledge-graph fact curation workflow."""

from __future__ import annotations

from typing import Dict, Iterable

from .facts import KnowledgeFact


class FactCurationService:
    """Validate and curate facts before they enter a graph backend."""

    def __init__(self, facts: Iterable[KnowledgeFact] = ()):
        self._facts: Dict[str, KnowledgeFact] = {}
        for fact in facts:
            self.add(fact)

    def add(self, fact: KnowledgeFact) -> KnowledgeFact:
        if fact.id in self._facts:
            raise ValueError(f"Fact '{fact.id}' already exists")
        self._validate(fact)
        self._facts[fact.id] = fact
        return fact

    def update(self, fact: KnowledgeFact) -> KnowledgeFact:
        if fact.id not in self._facts:
            raise KeyError(f"Fact '{fact.id}' not found")
        self._validate(fact)
        self._facts[fact.id] = fact
        return fact

    def get(self, fact_id: str) -> KnowledgeFact:
        if fact_id not in self._facts:
            raise KeyError(f"Fact '{fact_id}' not found")
        return self._facts[fact_id]

    def list(self) -> list[KnowledgeFact]:
        return list(self._facts.values())

    @staticmethod
    def _validate(fact: KnowledgeFact) -> None:
        if not fact.provenance.source.strip():
            raise ValueError("Fact provenance source is required")
        if not fact.provenance.curator:
            raise ValueError("Fact provenance curator is required for curation")
