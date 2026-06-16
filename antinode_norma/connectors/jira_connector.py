import asyncio
import os
from jira import JIRA
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "antinode_norma.server.mcp_server"]
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            jira = JIRA(
                server=os.getenv("JIRA_SERVER"),
                token_auth=os.getenv("JIRA_TOKEN")
            )
            issues = jira.search_issues('labels = bdd-ready')
            for issue in issues:
                raw_text = f"{issue.fields.summary}\n{issue.fields.description or ''}"
                result = await session.call_tool(
                    "submit_story",
                    arguments={
                        "raw_text": raw_text,
                        "role": "User",
                        "action": issue.fields.summary,
                        "benefit": "To be defined",
                        "acceptance_criteria": ["Define acceptance criteria in JIRA"]
                    }
                )
                print(f"Submitted {issue.key}: {result}")

if __name__ == "__main__":
    asyncio.run(main())