from typing import Optional


class StepMappingError(ValueError):
    """Raised when an LLM step mapping cannot be completed reliably."""

    def __init__(self, step_text: str, message: str, suggested_fixes: Optional[list[str]] = None):
        self.step_text = step_text
        self.suggested_fixes = suggested_fixes or []
        details = [message]
        if self.suggested_fixes:
            details.append("Suggested fixes: " + "; ".join(self.suggested_fixes))
        super().__init__(f"Step mapping failed for '{step_text}': {' | '.join(details)}")


class LLMTimeoutError(TimeoutError):
    """Raised when an LLM call exceeds the configured timeout."""

    def __init__(self, step_text: str, timeout: int, retry_guidance: Optional[str] = None):
        self.step_text = step_text
        self.timeout = timeout
        self.retry_guidance = retry_guidance or (
            "Retry with a shorter, more explicit step or increase the timeout in codegen.yaml."
        )
        super().__init__(
            f"LLM mapping timed out for '{step_text}' after {timeout}s. {self.retry_guidance}"
        )


class SelectorNotFoundError(LookupError):
    """Raised when no selector can be resolved for a step."""

    def __init__(self, selector: str, step_context: str, alternatives: Optional[list[str]] = None):
        self.selector = selector
        self.step_context = step_context
        self.alternatives = alternatives or []
        details = [f"Unable to find selector '{selector}' for step '{step_context}'."]
        if self.alternatives:
            details.append("Alternatives: " + "; ".join(self.alternatives))
        super().__init__(" ".join(details))
