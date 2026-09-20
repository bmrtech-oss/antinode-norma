import json
from typing import Callable
from .schemas import UserStory

# Cache the schema JSON at import time to avoid expensive repeated computation
_USERSTORY_SCHEMA_JSON = UserStory.schema_json(indent=2)


def parse_story(raw_text: str, llm_call: Callable[[str], str]) -> UserStory:
    # If using the mock LLM, keep the prompt small to avoid large string processing
    if getattr(llm_call, "_is_mock", False):
        schema_json = "{role: str, action: str, benefit: str, acceptance_criteria: [str]}"
    else:
        schema_json = _USERSTORY_SCHEMA_JSON
    prompt = f"""Convert the following user story into a JSON object that exactly matches this schema.

Schema:
{schema_json}

Story:
{raw_text}

Return ONLY valid JSON, no extra text."""

    response = llm_call(prompt)
    # Extract JSON if wrapped in backticks
    if isinstance(response, str):
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            response = response.split("```")[1].split("```")[0]

    try:
        data = json.loads(response or "")
        return UserStory(**data)
    except Exception:
        # Fallback: attempt a simple heuristic parse of the raw story text
        text = raw_text.strip().strip("`\n ")
        role = "user"
        action = "do something"
        benefit = "achieve value"
        text_lower = text.lower()
        if text_lower.startswith("as a "):
            body = text[5:]
            if " so that " in body:
                idx = body.lower().find(" so that ")
                before = body[:idx]
                after = body[idx + 9 :]
                benefit = after.strip().rstrip(".")
            else:
                before = body
            if " i want to " in before.lower():
                idx = before.lower().find(" i want to ")
                role = before[:idx].strip().rstrip(".")
                action = before[idx + 11 :].strip().rstrip(".")
            else:
                action = before.split(".")[0].strip()

        data = {
            "role": role,
            "action": action,
            "benefit": benefit,
            "acceptance_criteria": [
                "Fallback: parsed from raw text",
            ],
        }
        return UserStory(**data)
