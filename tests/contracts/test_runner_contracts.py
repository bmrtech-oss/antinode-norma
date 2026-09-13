import pytest
from unittest.mock import patch, MagicMock
from antinode_norma.runner import run_agent_from_raw
from antinode_norma.core.schemas import UserStory, QualityReport


@pytest.mark.asyncio
async def test_runner_contract_run_agent_from_raw_quality_only():
    story = UserStory(
        role="user", action="login", benefit="access system", acceptance_criteria=["passes"]
    )
    report = QualityReport(
        passes_invest=True, invest_details={}, issues=[], suggestions=[], quality_score=1.0
    )
    with (
        patch("antinode_norma.runner.get_llm_callable", return_value=MagicMock()),
        patch("antinode_norma.runner.parse_story", return_value=story),
        patch("antinode_norma.runner.compute_quality", return_value=report),
    ):
        res = await run_agent_from_raw("raw story", quality_only=True)
        assert isinstance(res, dict)
        assert "quality_score" in res
        assert "passes_invest" in res
        assert "issues" in res
        assert "suggestions" in res
