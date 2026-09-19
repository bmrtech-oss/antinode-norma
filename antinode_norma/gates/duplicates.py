from typing import List, Set
from antinode_norma.gates.types import BaseGate, GateContext
from antinode_norma.core.types import GateResult


class Q5DuplicatesGate(BaseGate):
    """
    Quality Gate Q5: No duplicate scenario names.
    Checks for duplicate scenario titles (Scenario / Scenario Outline) in Gherkin text.
    """

    gate_id: str = "Q5"
    is_hard_gate: bool = True

    def evaluate(self, context: GateContext) -> GateResult:
        lines = context.gherkin_text.splitlines()
        seen_titles: Set[str] = set()
        duplicate_titles: List[str] = []

        for line in lines:
            stripped = line.strip()
            title = None
            if stripped.startswith("Scenario:"):
                title = stripped[len("Scenario:") :].strip()
            elif stripped.startswith("Scenario Outline:"):
                title = stripped[len("Scenario Outline:") :].strip()

            if title:
                norm_title = " ".join(title.split()).lower()
                if norm_title in seen_titles:
                    if title not in duplicate_titles:
                        duplicate_titles.append(title)
                else:
                    seen_titles.add(norm_title)

        if not duplicate_titles:
            return GateResult(
                gate_id=self.gate_id,
                passed=True,
                score=1.0,
                issues=[],
                suggestions=[],
            )

        dups_str = ", ".join(f"'{t}'" for t in duplicate_titles)
        return GateResult(
            gate_id=self.gate_id,
            passed=False,
            score=0.0,
            issues=[f"Duplicate scenario title(s) detected: {dups_str}"],
            suggestions=["Ensure each Scenario and Scenario Outline has a unique descriptive title."],
        )
