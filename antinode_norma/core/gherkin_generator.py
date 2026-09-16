<<<<<<< HEAD
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
=======
from typing import Callable, List
from .schemas import UserStory
from .prompts import FEATURE_PROMPT_TEMPLATE, select_feature_examples
from .features import FeatureFlagResolver
from .agent import NormaAgent
from antinode_norma.ingest_structured.story import story_to_case


def generate_gherkin(
    story: UserStory, step_definitions: List[str], llm_call: Callable[[str], str]
) -> str:
    resolver = FeatureFlagResolver()
    if resolver.is_enabled("unified_agent"):
        story_dict = {
            "role": story.role,
            "action": story.action,
            "benefit": story.benefit,
            "acceptance_criteria": story.acceptance_criteria,
        }
        test_case = story_to_case(story_dict)
        agent = NormaAgent(llm_callable=llm_call)
        gherkin_text, verdict, attempts = agent.generate_feature_with_repair([test_case])
        return gherkin_text

    # Legacy path (when unified_agent flag is disabled)
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
>>>>>>> d4d2d9a (fix(tests): update CORS header assertion in test_api_p9_t01.py)
