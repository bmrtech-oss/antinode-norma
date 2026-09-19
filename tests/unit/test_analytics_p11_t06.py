"""Unit tests for Phase 11 Task P11-T06: Analytics Dashboard."""

from fastapi.testclient import TestClient

from antinode_norma.analytics import AnalyticsCollector
from antinode_norma.governance.approval import ApprovalGate
from antinode_norma.governance.audit import AuditLog
from antinode_norma.server.api import app


def test_analytics_collector():
    gate = ApprovalGate()
    req = gate.submit_request(feature_id="feat-1", gherkin_text="Feature: Test", requested_by="dev1")
    gate.approve(request_id=req.id, reviewer="qa1", reason="Looks good")

    audit = AuditLog()
    audit.record_event(action="test:action", resource="test:resource")

    collector = AnalyticsCollector(approval_gate=gate, audit_log=audit)
    summary = collector.collect_summary(feature_count=10)

    assert summary.throughput_features == 10
    assert summary.total_approvals == 1
    assert summary.approved_count == 1
    assert summary.approval_conversion_rate == 1.0
    assert summary.total_audit_events >= 1
    assert "daily_generations" in summary.trends


def test_analytics_api_endpoint():
    client = TestClient(app, headers={"X-User-ID": "admin_user"})

    res = client.get("/api/analytics/summary")
    assert res.status_code == 200
    data = res.json()
    assert "throughput_features" in data
    assert "quality_pass_rate" in data
    assert "approval_conversion_rate" in data
