import pytest
from unittest.mock import patch
from antinode_norma.agent import BDDAgent
from antinode_norma.agent_tools import AGENT_TOOLS


@pytest.mark.asyncio
async def test_agent_simple_goal():
    # Mock the LLM to return a specific action
    with patch("antinode_norma.agent.create_llm_callable") as mock_llm_factory:
        mock_llm = lambda p: '{"type": "finish", "reason": "done"}'
        mock_llm_factory.return_value = mock_llm
        agent = BDDAgent({}, AGENT_TOOLS)
        result = agent.run("Test goal")
        assert result["done"] is True
