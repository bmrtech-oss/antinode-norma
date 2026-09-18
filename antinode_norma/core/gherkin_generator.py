from typing import Callable, List
from .schemas import UserStory
from .prompts import FEATURE_PROMPT_TEMPLATE, select_feature_examples
from .features import FeatureFlagResolver
from .types import TestCase
from .agent import NormaAgent


def generate_gherkin(
    story: UserStory, step_definitions: List[str], llm_call: Callable[[str], str]
) -> str:
    resolver = FeatureFlagResolver()
    if resolver.is_enabled("unified_agent"):
        tc = TestCase(
            id=getattr(story, "id", "TC-001"),
            title=f"Feature for {story.action}",
            role=story.role,
            action=story.action,
            benefit=story.benefit,
            acceptance_criteria=story.acceptance_criteria,
        )
        agent = NormaAgent(llm_callable=llm_call)
        gherkin_text, _, _ = agent.generate_feature_with_repair([tc])
        return gherkin_text

    examples = select_feature_examples(story)
    prompt = FEATURE_PROMPT_TEMPLATE.format(
        examples="\n\n".join(examples),
        role=story.role,
        action=story.action,
        benefit=story.benefit,
        criteria="\n".join(f"- {c}" for c in story.acceptance_criteria),
    )

    # Include step definitions as optional guidance for reusable phrases.
    if step_definitions:
        extra = "\nExisting step definitions (reuse if possible):\n"
        extra += "\n".join(f"- {s}" for s in step_definitions)
        prompt = prompt.replace(
            "Output ONLY a valid Gherkin feature file.",
            f"{extra}\n\nOutput ONLY a valid Gherkin feature file.",
        )

    return llm_call(prompt)
