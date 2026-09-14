from typing import List, Optional, Tuple, Callable
from antinode_norma.core.types import TestCase, DomainModel, Verdict
from antinode_norma.core.prompts import build_feature_generation_prompt
from antinode_norma.gates.types import GateContext
from antinode_norma.gates.runner import GateRunner
from antinode_norma.core.features import FeatureFlagResolver
from antinode_norma.cache.exact import ExactPromptCache


class NormaAgent:
    """
    Unified BDD Agent Skeleton.
    Generates Gherkin feature files from TestCases and evaluates them using Quality Gates.
    Supports multi-attempt repair loop with error feedback and exact prompt caching.
    """

    def __init__(
        self,
        llm_callable: Callable[[str], str],
        domain_model: Optional[DomainModel] = None,
        gate_runner: Optional[GateRunner] = None,
        cache: Optional[ExactPromptCache] = None,
    ):
        self.llm_callable = llm_callable
        self.domain_model = domain_model
        self.gate_runner = gate_runner if gate_runner is not None else GateRunner()
        self.cache = cache

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

        resolver = FeatureFlagResolver()
        use_cache = resolver.is_enabled("cache_exact")

        gherkin_text: Optional[str] = None
        cache_inst = self.cache or (ExactPromptCache() if use_cache else None)

        if use_cache and cache_inst:
            gherkin_text = cache_inst.get(full_prompt)

        if gherkin_text is None:
            gherkin_text = self.llm_callable(full_prompt)
            if use_cache and cache_inst:
                cache_inst.set(full_prompt, gherkin_text)

        context = GateContext(
            gherkin_text=gherkin_text,
            test_cases=test_cases,
            domain_model=self.domain_model,
        )

        verdict = self.gate_runner.evaluate(context)
        return gherkin_text, verdict

    def generate_feature_with_repair(
        self,
        test_cases: List[TestCase],
        max_attempts: int = 3,
    ) -> Tuple[str, Verdict, int]:
        """
        Execute generation with repair loop up to max_attempts.

        If quality gates fail, extracts issues from failed gate results and feeds
        them back into the prompt for subsequent attempts.

        Args:
            test_cases: List of TestCase IR instances.
            max_attempts: Maximum number of generation attempts (default 3).

        Returns:
            Tuple of (gherkin_text, verdict, attempt_count).
        """
        feedback: Optional[List[str]] = None
        last_gherkin = ""
        last_verdict: Optional[Verdict] = None

        for attempt in range(1, max_attempts + 1):
            gherkin_text, verdict = self.generate_feature(
                test_cases=test_cases,
                feedback=feedback,
            )
            last_gherkin = gherkin_text
            last_verdict = verdict

            # Check if all hard gates passed (and overall pass condition met)
            if verdict.hard_pass:
                return gherkin_text, verdict, attempt

            # Construct feedback list from failed gate issues
            feedback = []
            for gate_id, gate_res in verdict.gate_results.items():
                if not gate_res.passed:
                    for issue in gate_res.issues:
                        feedback.append(f"[{gate_id}] {issue}")

        return last_gherkin, last_verdict, max_attempts
