"""Integration tests for runner with real LLM."""

import os
import pytest
from antinode_norma.runner import run_agent_from_raw


@pytest.mark.skipif(not os.getenv("OPENROUTER_API_KEY"),
                    reason="OPENROUTER_API_KEY not set")
@pytest.mark.asyncio
async def test_runner_end_to_end(sample_story_pass):
    result = await run_agent_from_raw(sample_story_pass)
    assert "feature_path" in result
    assert result["validation_passed"] is True
    import os

    assert os.path.exists(result["feature_path"])
