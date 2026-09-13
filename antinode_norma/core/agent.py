from typing import List, Optional, Tuple, Callable
from antinode_norma.core.types import TestCase, DomainModel, Verdict
from antinode_norma.core.prompts import build_feature_generation_prompt
from antinode_norma.gates.types import GateContext
from antinode_norma.gates.runner import GateRunner


class NormaAgent:
    """
    Unified BDD Agent Skeleton.
    Generates Gherkin feature files from TestCases and evaluates them using Quality Gates.
    """

    def __init__(
        self,
        llm_callable: Callable[[str], str],
        domain_model: Optional[DomainModel] = None,
        gate_runner: Optional[GateRunner] = None,
    ):
        self.llm_callable = llm_callable
        self.domain_model = domain_model
        self.gate_runner = gate_runner if gate_runner is not None else GateRunner()

    def generate_feature(
        self,
        test_cases: List[TestCase],
        feedback: Optional[List[str]] = None,
    ) -> Tuple[str, Verdict]:
        """
        Generate Gherkin feature text and evaluate it against quality gates.

        Args:
            test_cases: List of TestCase IR instances.
            feedback: Optional feedback messages from previous attempts.

        Returns:
            Tuple of (gherkin_text, verdict).
        """
        sys_prompt, user_prompt = build_feature_generation_prompt(
            test_cases=test_cases,
            domain_model=self.domain_model,
            feedback=feedback,
        )

        full_prompt = f"{sys_prompt}\n\n{user_prompt}"
        gherkin_text = self.llm_callable(full_prompt)

        context = GateContext(
            gherkin_text=gherkin_text,
            test_cases=test_cases,
            domain_model=self.domain_model,
        )

        verdict = self.gate_runner.evaluate(context)
        return gherkin_text, verdict
