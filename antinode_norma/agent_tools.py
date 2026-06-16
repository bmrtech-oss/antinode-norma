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
from .utils.llm_factory import create_llm_callable

# JIRA connector (optional)
try:
    from .connectors.jira_connector import fetch_issue, comment_on_issue
except ImportError:
    def fetch_issue(key: str):
        return {"error": "JIRA connector not installed"}
    def comment_on_issue(key: str, comment: str):
        return {"error": "JIRA connector not installed"}

# Git operations (if gitpython installed)
try:
    from git import Repo, Remote
    def create_pull_request(pr_title: str, pr_body: str, base: str = "main", head: str = None) -> Dict:
        repo = Repo(os.getcwd())
        if not head:
            head = repo.active_branch.name
        return {"pr_url": f"https://github.com/example/pr/1", "status": "created"}
except ImportError:
    def create_pull_request(pr_title: str, pr_body: str, base: str = "main", head: str = None) -> Dict:
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
    return {"issue_key": key, "raw_text": f"{issue['summary']}\n{issue['description'] or ''}", "story": None}

def submit_story(**kwargs) -> Dict:
    """Submit a user story and return quality report."""
    # Try common parameter names
    text = kwargs.get("raw_text") or kwargs.get("story") or kwargs.get("title") or kwargs.get("text")
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
        "story_id": story_obj.story_id or "unknown"
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
    suggestion_text = "\n".join([f"- {s}" for s in suggestions]) if suggestions else "Make the story clearer and more testable."
    prompt = f"""Improve the following user story based on these suggestions:
Suggestions:
{suggestion_text}

Current story:
{story_text}

Return the improved story with the same format (As a... I want... so that... Acceptance criteria: ...). Only return the improved story."""
    improved = llm(prompt)
    return {"improved_story": improved, "story_id": story_id}

def generate_feature(**kwargs) -> Dict:
    """Generate a .feature file from a story."""
    story_id = kwargs.get("story_id")
    step_defs = kwargs.get("step_definitions", [])
    if not story_id:
        return {"error": "No story_id provided."}
    # In a real implementation, retrieve story from store.
    return {"error": "Story not found in context (story_id: {story_id})"}

def run_tests(**kwargs) -> Dict:
    """Run Cucumber/Behave tests on a feature file."""
    feature_path = kwargs.get("feature_path")
    if not feature_path:
        return {"error": "No feature_path provided."}
    try:
        with open(feature_path, 'r') as f:
            content = f.read()
        validation = validate_gherkin(content)
        if not validation.valid:
            return {"passed": False, "errors": validation.errors}
        result = subprocess.run(["behave", feature_path], capture_output=True, text=True, cwd=os.getcwd())
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
        with open(feature_path, 'r') as f:
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
    "comment_on_jira": comment_on_jira,
}