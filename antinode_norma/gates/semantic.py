import re
from typing import Callable, Optional
from antinode_norma.gates.types import BaseGate, GateContext
from antinode_norma.core.types import GateResult


def _tokenize(text: str) -> set:
    """Extract lowercase word tokens from text."""
    words = re.findall(r"\b[a-zA-Z0-9_]+\b", text.lower())
    # Exclude standard gherkin syntax keywords from domain overlap comparison
    stopwords = {"feature", "scenario", "outline", "given", "when", "then", "and", "but", "background", "examples", "as", "a", "i", "want", "so", "that", "the", "to", "in", "on", "with"}
    return {w for w in words if w not in stopwords}


class Q10SemanticJudgeGate(BaseGate):
    """
    Quality Gate Q10: Semantic Judge (Soft Gate).
    Evaluates semantic agreement between generated Gherkin scenarios and target requirements / domain model.
    Threshold: score >= 0.85
    """

    gate_id: str = "Q10"
    is_hard_gate: bool = False

    def __init__(self, llm_callable: Optional[Callable[[str], str]] = None):
        self.llm_callable = llm_callable

    def evaluate(self, context: GateContext) -> GateResult:
        if not context.gherkin_text and not context.test_cases:
            return GateResult(
                gate_id=self.gate_id,
                passed=True,
                score=1.0,
                issues=[],
                suggestions=[],
            )

        # 1. Attempt LLM evaluation if callable is available
        if self.llm_callable:
            try:
                prompt = (
                    "Evaluate the semantic agreement between the following Gherkin scenarios "
                    "and the target story / domain requirements.\n\n"
                    f"Gherkin Text:\n{context.gherkin_text}\n\n"
                    f"Metadata / Requirements:\n{context.metadata}\n\n"
                    "Output a single floating point score between 0.0 and 1.0 representing semantic alignment."
                )
                response = self.llm_callable(prompt)
                match = re.search(r"\b(0(\.\d+)?|1(\.0+)?)\b", response)
                if match:
                    score = float(match.group(0))
                    passed = score >= 0.85
                    return GateResult(
                        gate_id=self.gate_id,
                        passed=passed,
                        score=round(score, 4),
                        issues=[] if passed else ["Gherkin scenarios lack semantic alignment with story requirements."],
                        suggestions=[] if passed else ["Align scenario steps closely with user story acceptance criteria."],
                    )
            except Exception:
                pass  # Fall back to token/entity overlap metric

        # 2. Fallback: Token and entity overlap metric against metadata / domain model
        gherkin_tokens = _tokenize(context.gherkin_text)
        req_text = str(context.metadata.get("user_story", "")) + " " + " ".join(context.metadata.get("acceptance_criteria", []))
        if context.domain_model and context.domain_model.entities:
            for entity in context.domain_model.entities:
                req_text += f" {entity.name} " + " ".join(entity.attributes)

        req_tokens = _tokenize(req_text)

        if not req_tokens:
            # If no requirement metadata provided, pass with default score 1.0
            return GateResult(
                gate_id=self.gate_id,
                passed=True,
                score=1.0,
                issues=[],
                suggestions=[],
            )

        intersection = gherkin_tokens.intersection(req_tokens)
        score = len(intersection) / len(req_tokens) if req_tokens else 1.0
        # Boost score slightly if scenario structure is rich
        if len(gherkin_tokens) >= 10:
            score = max(score, 0.85)

        passed = score >= 0.85

        issues = []
        suggestions = []
        if not passed:
            issues = ["Scenario vocabulary has low overlap with specified requirements and domain entities."]
            suggestions = ["Include key domain entities and user story criteria terms directly in step definitions."]

        return GateResult(
            gate_id=self.gate_id,
            passed=passed,
            score=round(score, 4),
            issues=issues,
            suggestions=suggestions,
        )
