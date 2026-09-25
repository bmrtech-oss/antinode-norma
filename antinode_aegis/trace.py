"""A2 traceability matrix construction and rendering."""

from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List

from pydantic import BaseModel, Field


class TraceItem(BaseModel):
    requirement_id: str
    requirement_title: str
    scenario_title: str = ""
    tags: List[str] = Field(default_factory=list)
    status: str = "UNCOVERED"


class TraceMatrix(BaseModel):
    feature_title: str = "Unknown Feature"
    items: List[TraceItem] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TraceRenderer:
    """Render requirement-to-scenario coverage for the Aegis package."""

    @staticmethod
    def build_matrix(
        *,
        feature_title: str,
        requirements: Iterable[Dict[str, str]],
        scenarios: Iterable[Dict[str, Any]],
        metadata: Dict[str, Any] | None = None,
    ) -> TraceMatrix:
        scenario_by_requirement: Dict[str, Dict[str, Any]] = {}
        for scenario in scenarios:
            for requirement_id in scenario.get("requirement_ids", []):
                scenario_by_requirement[requirement_id] = scenario

        items: List[TraceItem] = []
        for requirement in requirements:
            requirement_id = requirement["id"]
            scenario = scenario_by_requirement.get(requirement_id)
            items.append(
                TraceItem(
                    requirement_id=requirement_id,
                    requirement_title=requirement["title"],
                    scenario_title=scenario.get("title", "") if scenario else "",
                    tags=list(scenario.get("tags", [])) if scenario else [],
                    status="COVERED" if scenario else "UNCOVERED",
                )
            )

        return TraceMatrix(feature_title=feature_title, items=items, metadata=metadata or {})

    @staticmethod
    def render_json(matrix: TraceMatrix) -> str:
        return json.dumps(matrix.model_dump(), sort_keys=True, indent=2)

    @staticmethod
    def render_markdown(matrix: TraceMatrix) -> str:
        lines = [
            f"# Aegis Traceability — {matrix.feature_title}",
            "",
            "| Requirement ID | Requirement | Scenario | Tags | Status |",
            "|---|---|---|---|---|",
        ]
        for item in matrix.items:
            tags = ", ".join(item.tags) if item.tags else "-"
            lines.append(
                f"| `{item.requirement_id}` | {item.requirement_title} | "
                f"{item.scenario_title or '-'} | `{tags}` | **{item.status}** |"
            )
        return "\n".join(lines)
