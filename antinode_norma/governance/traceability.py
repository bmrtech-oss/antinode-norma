import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from antinode_norma.core.types import TestCase, DomainModel


class TraceableItem(BaseModel):
    requirement_id: str
    requirement_title: str
    scenario_title: str
    tags: List[str] = Field(default_factory=list)
    status: str = "COVERED"


class TraceabilityMatrix(BaseModel):
    feature_title: str = "Unknown Feature"
    items: List[TraceableItem] = Field(default_factory=list)
    uncovered_requirements: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TraceabilityRenderer:
    @staticmethod
    def build_matrix(
        gherkin_text: str = "",
        test_cases: Optional[List[TestCase]] = None,
        domain_model: Optional[DomainModel] = None,
    ) -> TraceabilityMatrix:
        items: List[TraceableItem] = []
        feature_title = "Unknown Feature"
        uncovered: List[str] = []

        if test_cases:
            for tc in test_cases:
                req_id = tc.id
                req_title = tc.title
                items.append(
                    TraceableItem(
                        requirement_id=req_id,
                        requirement_title=req_title,
                        scenario_title=tc.title,
                        tags=tc.tags,
                        status="COVERED",
                    )
                )

        if gherkin_text:
            lines = gherkin_text.splitlines()
            current_tags: List[str] = []
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("Feature:"):
                    feature_title = stripped[len("Feature:") :].strip()
                elif stripped.startswith("@"):
                    current_tags = [t.strip() for t in stripped.split() if t.startswith("@")]
                elif stripped.startswith("Scenario:") or stripped.startswith("Scenario Outline:"):
                    scenario_title = stripped.split(":", 1)[1].strip()
                    tc_tags = [t for t in current_tags if t.startswith("@TC-") or t.startswith("@REQ-")]
                    req_id = tc_tags[0] if tc_tags else "@TC-UNMAPPED"
                    items.append(
                        TraceableItem(
                            requirement_id=req_id,
                            requirement_title=f"Requirement for {scenario_title}",
                            scenario_title=scenario_title,
                            tags=current_tags,
                            status="COVERED",
                        )
                    )
                    current_tags = []

        return TraceabilityMatrix(
            feature_title=feature_title,
            items=items,
            uncovered_requirements=uncovered,
        )

    @staticmethod
    def render_markdown(matrix: TraceabilityMatrix) -> str:
        lines = [
            f"# Traceability Matrix — {matrix.feature_title}",
            "",
            "| Requirement ID | Requirement / Case Title | Covered Scenario | Tags | Status |",
            "|---|---|---|---|---|",
        ]
        for item in matrix.items:
            tags_str = ", ".join(item.tags) if item.tags else "-"
            lines.append(
                f"| `{item.requirement_id}` | {item.requirement_title} | {item.scenario_title} | `{tags_str}` | **{item.status}** |"
            )

        if matrix.uncovered_requirements:
            lines.extend([
                "",
                "## Uncovered Requirements",
                "",
            ])
            for unreq in matrix.uncovered_requirements:
                lines.append(f"- ⚠️ {unreq}")

        return "\n".join(lines)

    @staticmethod
    def render_json(matrix: TraceabilityMatrix) -> str:
        return json.dumps(matrix.model_dump(), indent=2)
