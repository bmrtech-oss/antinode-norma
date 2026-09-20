import json
from typing import Callable
from .schemas import UserStory


def parse_story(raw_text: str, llm_call: Callable[[str], str]) -> UserStory:
    schema_json = UserStory.schema_json(indent=2)
    prompt = f"""Convert the following user story into a JSON object that exactly matches this schema.

Schema:
{schema_json}

Story:
{raw_text}

Return ONLY valid JSON, no extra text."""

    response = llm_call(prompt)
    # Extract JSON if wrapped in backticks
    if "```json" in response:
        response = response.split("```json")[1].split("```")[0]
    elif "```" in response:
        response = response.split("```")[1].split("```")[0]
    data = json.loads(response)
    return UserStory(**data)
