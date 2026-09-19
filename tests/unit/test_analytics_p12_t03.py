"""
Unit tests for Phase 12 Task P12-T03: Analytics polish.
"""

from antinode_norma.analytics.metrics import AnalyticsCollector, AnalyticsSummary
from antinode_norma.execution.history import ExecutionHistoryStore, ExecutionHistoryRecord
from antinode_norma.evaluate.cost import CostTracker


def test_analytics_summary_default_fields():
    summary = AnalyticsSummary()
    assert summary.total_executions == 0
    assert summary.execution_pass_rate == 0.0
    assert summary.flake_rate == 0.0
    assert summary.total_cost_usd == 0.0
    assert summary.avg_cost_per_run == 0.0


def test_analytics_collector_with_execution_and_cost(tmp_path):
    history_file = str(tmp_path / "execution_history.json")
    history_store = ExecutionHistoryStore(history_file=history_file)
    history_store.save_run(
        ExecutionHistoryRecord(
            id="run-1",
            status="PASSED",
            total_scenarios=2,
            passed_scenarios=2,
            failed_scenarios=0,
        )
    )
    history_store.save_run(
        ExecutionHistoryRecord(
            id="run-2",
            status="DEGRADED",
            total_scenarios=2,
            passed_scenarios=1,
            failed_scenarios=1,
        )
    )

    cost_log_path = tmp_path / "llm_cost.jsonl"
    cost_tracker = CostTracker(log_path=cost_log_path)
    cost_tracker.log_call(
        prompt="Sample prompt",
        completion="Sample completion",
        input_tokens=2000,
        output_tokens=1000,
    )

    collector = AnalyticsCollector(
        execution_store=history_store,
        cost_tracker=cost_tracker,
    )

    summary = collector.collect_summary(feature_count=5)
    assert summary.throughput_features == 5
    assert summary.total_executions == 2
    assert summary.execution_pass_rate == 0.5
    assert summary.flake_rate == 0.5
    assert summary.total_cost_usd > 0.0
    assert summary.avg_cost_per_run > 0.0
    assert "cost_usd" in summary.trends
