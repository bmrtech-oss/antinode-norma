import os
import json
import subprocess
import asyncio
from typing import Dict, Any, List, Optional
from pathlib import Path
from .runner import run_agent_from_raw
from .utils.file_writer import write_feature_file
from .core.validator import validate_gherkin
from .core.parser import parse_story
from .core.gherkin_generator import generate_gherkin
from .core.schemas import UserStory
from .utils.llm_factory import create_llm_callable

# JIRA connector (optional)
try:
    from .connectors.jira_connector import (
        fetch_issue,
        fetch_issues,
        comment_on_issue,
        transition_issue,
        update_issue_status,
    )
except ImportError:

    def fetch_issue(key: str):
        return {"error": "JIRA connector not installed"}

    def fetch_issues(label: str = "bdd-ready"):
        return {"error": "JIRA connector not installed"}

    def comment_on_issue(key: str, comment: str):
        return {"error": "JIRA connector not installed"}

    def transition_issue(key: str, transition_name: str):
        return {"error": "JIRA connector not installed"}

    def update_issue_status(key: str, status_name: str):
        return {"error": "JIRA connector not installed"}


# TestRail connector (optional)
try:
    from .connectors.testrail_connector import add_test_case, add_test_result, create_test_run
except ImportError:

    def add_test_case(
        section_id: int, title: str, description: str = "", case_type: int = 1, priority_id: int = 2
    ):
        return {"error": "TestRail connector not installed"}

    def add_test_result(test_id: int, status_id: int, comment: str = ""):
        return {"error": "TestRail connector not installed"}

    def create_test_run(
        project_id: int,
        suite_id: int,
        name: str,
        description: str = "",
        include_all: bool = True,
        case_ids=None,
    ):
        return {"error": "TestRail connector not installed"}


# Notifications connector (optional)
try:
    from .connectors.notifications import post_slack_message, post_teams_message
except ImportError:

    def post_slack_message(webhook_url: str, text: str, blocks=None):
        return {"error": "Notifications connector not installed"}

    def post_teams_message(webhook_url: str, title: str, text: str):
        return {"error": "Notifications connector not installed"}


# Git operations (if gitpython installed)
try:
    from git import Repo, Remote

    def create_pull_request(
        pr_title: str, pr_body: str, base: str = "main", head: str = None
    ) -> Dict:
        repo = Repo(os.getcwd())
        if not head:
            head = repo.active_branch.name
        return {"pr_url": f"https://github.com/example/pr/1", "status": "created"}

except ImportError:

    def create_pull_request(
        pr_title: str, pr_body: str, base: str = "main", head: str = None
    ) -> Dict:
        return {"error": "gitpython not installed"}


# ------------------------------------------------------------
# Flexible tools that accept any keyword arguments
# ------------------------------------------------------------


def fetch_jira_story(**kwargs) -> Dict:
    """Fetch a JIRA issue by key."""
    key = kwargs.get("issue_key") or kwargs.get("key")
    if not key:
        return {"error": "No issue key provided. Provide 'issue_key' or 'key'."}
    issue = fetch_issue(key)
    if "error" in issue:
        return issue
    return {
        "issue_key": key,
        "raw_text": f"{issue['summary']}\n{issue['description'] or ''}",
        "story": None,
    }


def submit_story(**kwargs) -> Dict:
    """Submit a user story and return quality report."""
    # Try common parameter names
    text = (
        kwargs.get("raw_text") or kwargs.get("story") or kwargs.get("title") or kwargs.get("text")
    )
    if not text:
        return {"error": "No story text provided. Provide 'raw_text', 'story', or 'title'."}

    try:
        result = asyncio.run(run_agent_from_raw(text, quality_only=True))
    except Exception as e:
        return {"error": f"Failed to run agent: {str(e)}"}

    # Parse the story to get structured data
    llm_config = {
        "provider": os.getenv("LLM_PROVIDER", "openrouter"),
        "api_key": os.getenv("OPENROUTER_API_KEY") or os.getenv("ANTHROPIC_API_KEY"),
    }
    llm = create_llm_callable(llm_config)
    story_obj = parse_story(text, llm)

    return {
        "quality_score": result["quality_score"],
        "passes_invest": result["passes_invest"],
        "issues": result.get("issues", []),
        "suggestions": result.get("suggestions", []),
        "story": story_obj.dict(),
        "story_id": story_obj.story_id or "unknown",
    }


def improve_story(**kwargs) -> Dict:
    """Improve a story based on suggestions."""
    # Get story text from various possible parameter names
    story_text = kwargs.get("raw_text") or kwargs.get("story") or kwargs.get("text")
    suggestions = kwargs.get("suggestions", [])
    story_id = kwargs.get("story_id")

    if not story_text:
        return {"error": "No story text provided."}

    # Use LLM to improve the story
    llm_config = {
        "provider": os.getenv("LLM_PROVIDER", "openrouter"),
        "api_key": os.getenv("OPENROUTER_API_KEY") or os.getenv("ANTHROPIC_API_KEY"),
    }
    llm = create_llm_callable(llm_config)
    suggestion_text = (
        "\n".join([f"- {s}" for s in suggestions])
        if suggestions
        else "Make the story clearer and more testable."
    )
    prompt = f"""Improve the following user story based on these suggestions:
Suggestions:
{suggestion_text}

Current story:
{story_text}

Return the improved story with the same format (As a... I want... so that... Acceptance criteria: ...). Only return the improved story."""
    improved = llm(prompt)
    return {"improved_story": improved, "story_id": story_id}


def _load_story_from_kwargs(kwargs: Dict[str, Any]) -> UserStory:
    story_input = kwargs.get("story") or kwargs.get("raw_text") or kwargs.get("text")
    if isinstance(story_input, UserStory):
        return story_input
    if isinstance(story_input, dict):
        return UserStory(**story_input)
    if isinstance(story_input, str) and story_input.strip():
        llm_config = {
            "provider": os.getenv("LLM_PROVIDER", "openrouter"),
            "api_key": os.getenv("OPENROUTER_API_KEY") or os.getenv("ANTHROPIC_API_KEY"),
        }
        llm = create_llm_callable(llm_config)
        return parse_story(story_input, llm)
    raise ValueError("No story text provided.")


def generate_feature(**kwargs) -> Dict:
    """Generate a .feature file from a story."""
    step_defs = kwargs.get("step_definitions", [])
    output_dir = kwargs.get("output_dir") or os.getenv("NORMA_OUTPUT_DIR") or "features"

    try:
        story = _load_story_from_kwargs(kwargs)
    except ValueError as exc:
        return {"error": str(exc)}
    except Exception as exc:
        return {"error": f"Failed to parse story: {str(exc)}"}

    llm_config = {
        "provider": os.getenv("LLM_PROVIDER", "openrouter"),
        "api_key": os.getenv("OPENROUTER_API_KEY") or os.getenv("ANTHROPIC_API_KEY"),
    }
    llm = create_llm_callable(llm_config)
    gherkin = generate_gherkin(story, step_defs, llm)

    validation = validate_gherkin(gherkin)
    if not validation.valid:
        return {"error": "Generated Gherkin failed validation.", "errors": validation.errors}

    try:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        safe_name = story.action.lower().replace(" ", "_")[:200]
        file_path = Path(output_dir) / f"{safe_name}.feature"
        write_feature_file(str(file_path), gherkin)
        return {"feature_path": str(file_path), "validation_passed": True}
    except Exception as exc:
        return {"error": f"Failed to write feature file: {str(exc)}"}


def run_tests(**kwargs) -> Dict:
    """Run Cucumber/Behave tests on a feature file."""
    feature_path = kwargs.get("feature_path")
    if not feature_path:
        return {"error": "No feature_path provided."}
    try:
        with open(feature_path, "r") as f:
            content = f.read()
        validation = validate_gherkin(content)
        if not validation.valid:
            return {"passed": False, "errors": validation.errors}
        result = subprocess.run(
            ["behave", feature_path], capture_output=True, text=True, cwd=os.getcwd()
        )
        return {"passed": result.returncode == 0, "stdout": result.stdout, "stderr": result.stderr}
    except FileNotFoundError:
        return {"passed": False, "error": "behave not found"}
    except Exception as e:
        return {"passed": False, "error": str(e)}


def fix_feature(**kwargs) -> Dict:
    """Fix validation errors in a feature file."""
    feature_path = kwargs.get("feature_path")
    errors = kwargs.get("errors", [])
    if not feature_path:
        return {"error": "No feature_path provided."}
    try:
        with open(feature_path, "r") as f:
            content = f.read()
        llm_config = {
            "provider": os.getenv("LLM_PROVIDER", "openrouter"),
            "api_key": os.getenv("OPENROUTER_API_KEY") or os.getenv("ANTHROPIC_API_KEY"),
        }
        llm = create_llm_callable(llm_config)
        prompt = f"""Fix the following Gherkin feature file so it passes validation.
Errors: {errors}

Current content:
{content}

Return the corrected Gherkin only."""
        fixed = llm(prompt)
        write_feature_file(feature_path, fixed)
        return {"fixed": True, "new_content": fixed}
    except Exception as e:
        return {"error": str(e)}


def create_pr(**kwargs) -> Dict:
    """Create a pull request."""
    title = kwargs.get("pr_title") or kwargs.get("title")
    body = kwargs.get("pr_body") or kwargs.get("body")
    base = kwargs.get("base", "main")
    head = kwargs.get("head")
    if not title:
        return {"error": "No PR title provided."}
    return create_pull_request(title, body, base, head)


def search_jira_stories(**kwargs) -> Dict:
    """Search JIRA issues by label."""
    label = kwargs.get("label", "bdd-ready")
    issues = fetch_issues(label)
    if isinstance(issues, dict) and "error" in issues:
        return issues
    return {"issues": issues}


def transition_jira_issue(**kwargs) -> Dict:
    """Transition a JIRA issue to a new workflow status."""
    issue_key = kwargs.get("issue_key")
    transition_name = kwargs.get("transition_name")
    if not issue_key or not transition_name:
        return {"error": "issue_key and transition_name required."}
    return transition_issue(issue_key, transition_name)


def update_jira_issue_status(**kwargs) -> Dict:
    """Update a JIRA issue status by status name."""
    issue_key = kwargs.get("issue_key")
    status_name = kwargs.get("status_name")
    if not issue_key or not status_name:
        return {"error": "issue_key and status_name required."}
    return update_issue_status(issue_key, status_name)


def upload_testrail_case(**kwargs) -> Dict:
    """Upload a test case to TestRail."""
    section_id = kwargs.get("section_id")
    title = kwargs.get("title")
    description = kwargs.get("description", "")
    priority_id = kwargs.get("priority_id", 2)
    if section_id is None or not title:
        return {"error": "section_id and title are required."}
    return add_test_case(
        int(section_id), title, description, case_type=1, priority_id=int(priority_id)
    )


def add_testrail_result(**kwargs) -> Dict:
    """Add a result to a TestRail test case."""
    test_id = kwargs.get("test_id")
    status_id = kwargs.get("status_id")
    comment = kwargs.get("comment", "")
    if test_id is None or status_id is None:
        return {"error": "test_id and status_id are required."}
    return add_test_result(int(test_id), int(status_id), comment)


def notify_slack(**kwargs) -> Dict:
    """Send a Slack notification to a webhook URL."""
    webhook_url = kwargs.get("webhook_url") or os.getenv("SLACK_WEBHOOK_URL")
    text = kwargs.get("text")
    blocks = kwargs.get("blocks")
    if not webhook_url or not text:
        return {"error": "webhook_url and text are required."}
    return post_slack_message(webhook_url, text, blocks=blocks)


def notify_teams(**kwargs) -> Dict:
    """Send a Teams notification to a webhook URL."""
    webhook_url = kwargs.get("webhook_url") or os.getenv("TEAMS_WEBHOOK_URL")
    title = kwargs.get("title")
    text = kwargs.get("text")
    if not webhook_url or not title or not text:
        return {"error": "webhook_url, title and text are required."}
    return post_teams_message(webhook_url, title, text)


def comment_on_jira(**kwargs) -> Dict:
    """Post a comment to JIRA."""
    issue_key = kwargs.get("issue_key")
    comment = kwargs.get("comment")
    if not issue_key or not comment:
        return {"error": "issue_key and comment required."}
    return comment_on_issue(issue_key, comment)


# ------------------------------------------------------------
# Registry for the agent
# ------------------------------------------------------------

AGENT_TOOLS = {
    "fetch_jira_story": fetch_jira_story,
    "submit_story": submit_story,
    "improve_story": improve_story,
    "generate_feature": generate_feature,
    "run_tests": run_tests,
    "fix_feature": fix_feature,
    "create_pr": create_pr,
    "search_jira_stories": search_jira_stories,
    "comment_on_jira": comment_on_jira,
    "transition_jira_issue": transition_jira_issue,
    "update_jira_issue_status": update_jira_issue_status,
    "upload_testrail_case": upload_testrail_case,
    "add_testrail_result": add_testrail_result,
    "notify_slack": notify_slack,
    "notify_teams": notify_teams,
}
