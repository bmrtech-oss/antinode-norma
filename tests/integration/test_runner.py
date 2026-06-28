"""Integration tests for runner with real LLM."""

import os
import pytest
from antinode_norma.runner import run_agent_from_raw
from tests.conftest import maybe_skip_transient_llm_error


@pytest.mark.external_integration
@pytest.mark.asyncio
async def test_runner_end_to_end(sample_story_pass):
    try:
        result = await run_agent_from_raw(sample_story_pass)
    except Exception as exc:
        maybe_skip_transient_llm_error(exc)
        raise
    assert "feature_path" in result
    assert result["validation_passed"] is True
    assert os.path.exists(result["feature_path"])
