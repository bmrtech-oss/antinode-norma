from typing import Callable, List
from .schemas import UserStory
from .prompts import FEATURE_PROMPT_TEMPLATE, select_feature_examples


def generate_gherkin(
    story: UserStory, step_definitions: List[str], llm_call: Callable[[str], str]
) -> str:
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
