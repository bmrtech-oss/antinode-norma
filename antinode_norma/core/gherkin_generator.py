from typing import Callable, List
from .schemas import UserStory

def generate_gherkin(story: UserStory, step_definitions: List[str], llm_call: Callable[[str], str]) -> str:
    prompt = f"""You are a BDD expert. Write a Gherkin .feature file for the following user story.

User story:
Role: {story.role}
Action: {story.action}
Benefit: {story.benefit}
Acceptance criteria:
{chr(10).join('- ' + c for c in story.acceptance_criteria)}

Existing step definitions (reuse if possible):
{chr(10).join('- ' + s for s in step_definitions)}

Output ONLY the Gherkin content. Use format: Feature: ... Scenario: ... Given ... When ... Then ..."""

    return llm_call(prompt)