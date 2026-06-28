import asyncio
import os
from typing import List, Dict

try:
    from jira import JIRA
except ImportError:  # pragma: no cover
    JIRA = None

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def get_jira_client() -> JIRA:
    if JIRA is None:
        raise ImportError("The jira package is required for the JIRA connector.")
    server = os.getenv("JIRA_SERVER")
    token = os.getenv("JIRA_TOKEN")
    if not server or not token:
        raise EnvironmentError(
            "JIRA_SERVER and JIRA_TOKEN must be set to use the JIRA connector."
        )
    return JIRA(server=server, token_auth=token)


def fetch_issue(issue_key: str) -> Dict:
    jira = get_jira_client()
    issue = jira.issue(issue_key)
    return {
        "issue_key": issue.key,
        "summary": issue.fields.summary,
        "description": issue.fields.description or "",
        "status": getattr(issue.fields.status, "name", "unknown"),
        "labels": list(getattr(issue.fields, "labels", [])),
    }


def fetch_issues(label: str = "bdd-ready") -> List[Dict]:
    jira = get_jira_client()
    query = f"labels = {label}"
    issues = jira.search_issues(query)
    return [
        {
            "issue_key": issue.key,
            "summary": issue.fields.summary,
            "description": issue.fields.description or "",
            "status": getattr(issue.fields.status, "name", "unknown"),
            "labels": list(getattr(issue.fields, "labels", [])),
        }
        for issue in issues
    ]


def comment_on_issue(issue_key: str, comment: str) -> Dict:
    jira = get_jira_client()
    issue = jira.issue(issue_key)
    jira_comment = jira.add_comment(issue, comment)
    return {
        "issue_key": issue_key,
        "comment_id": getattr(jira_comment, "id", None),
        "comment_body": comment,
        "status": "posted",
    }


def transition_issue(issue_key: str, transition_name: str) -> Dict:
    jira = get_jira_client()
    issue = jira.issue(issue_key)
    transitions = jira.transitions(issue)
    transition = next(
        (t for t in transitions if t["name"].lower() == transition_name.lower()),
        None,
    )
    if transition is None:
        available = [t["name"] for t in transitions]
        raise ValueError(
            f"Transition '{transition_name}' not found. Available transitions: {available}"
        )
    jira.transition_issue(issue, transition["id"])
    return {
        "issue_key": issue_key,
        "transition": transition["name"],
        "status": "updated",
    }


def update_issue_status(issue_key: str, status_name: str) -> Dict:
    return transition_issue(issue_key, status_name)


async def main():
    server_params = StdioServerParameters(
        command="python", args=["-m", "antinode_norma.server.mcp_server"]
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            issues = fetch_issues("bdd-ready")
            for issue in issues:
                raw_text = f"{issue['summary']}\n{issue['description']}"
                result = await session.call_tool(
                    "submit_story",
                    arguments={
                        "raw_text": raw_text,
                        "role": "User",
                        "action": issue["summary"],
                        "benefit": "To be defined",
                        "acceptance_criteria": ["Define acceptance criteria in JIRA"],
                        "story_id": issue["issue_key"],
                    },
                )
                print(f"Submitted {issue['issue_key']}: {result}")


if __name__ == "__main__":
    asyncio.run(main())
