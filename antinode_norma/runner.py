import os
from typing import Dict, Any
from dotenv import load_dotenv

from .core.quality import compute_quality
from .core.parser import parse_story
from .core.gherkin_generator import generate_gherkin
from .core.validator import validate_gherkin
from .utils.llm_factory import create_llm_callable
from .utils.file_writer import write_feature_file

load_dotenv()


def get_llm_callable():
    config = {
        "provider": os.getenv("LLM_PROVIDER", "anthropic"),
        "api_key": os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY"),
        "model": os.getenv("LLM_MODEL"),
        "temperature": float(os.getenv("LLM_TEMPERATURE", "0.2")),
        "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "1024")),
        "url": os.getenv("LLM_URL"),
    }
    return create_llm_callable(config)


def get_step_definitions(keyword: str = None):
    steps = [
        "Given the user is on the login page",
        "When the user clicks 'Forgot password'",
        "Then a password reset email is sent",
        "Given a valid reset token exists",
        "When the user submits a new password",
        "Then the password is updated",
    ]
    if keyword:
        steps = [s for s in steps if s.lower().startswith(keyword.lower())]
    return steps


async def run_agent_from_raw(
    raw_story: str, quality_only: bool = False
) -> Dict[str, Any]:
    """Run the Norma agent from raw story text."""
    llm_call = get_llm_callable()
    story = parse_story(raw_story, llm_call)
    report = compute_quality(story)
    if quality_only:
        return {
            "quality_score": report.quality_score,
            "passes_invest": report.passes_invest,
            "issues": report.issues,
            "suggestions": report.suggestions,
        }
    if not report.passes_invest:
        return {
            "error": "Quality check failed – story does not meet INVEST criteria",
            "issues": report.issues,
            "suggestions": report.suggestions,
        }
    step_defs = get_step_definitions()
    gherkin = generate_gherkin(story, step_defs, llm_call)
    validation = validate_gherkin(gherkin)
    if not validation.valid:
        return {"error": "Gherkin validation failed", "errors": validation.errors}
    output_dir = os.getenv("NORMA_OUTPUT_DIR", "features")
    safe_action = story.action.lower().replace(" ", "_")
    file_path = os.path.join(output_dir, f"{safe_action}.feature")
    write_feature_file(file_path, gherkin)
    return {"feature_path": file_path, "validation_passed": True}


async def run_bdd_agent(raw_story: str, max_iterations: int = 3) -> Dict[str, Any]:
    """Run the autonomous BDD agent on a story."""
    return await run_agent_from_raw(raw_story)
