"""Cross-track regression integration tests for Phase 12 Task P12-T01."""

from fastapi.testclient import TestClient

from antinode_norma.analytics import AnalyticsCollector
from antinode_norma.collaboration import CommentStore, NotificationManager, Notification
from antinode_norma.core.agent import NormaAgent
from antinode_norma.ecosystem import (
    PluginHookRunner,
    PluginLifecycleManager,
    PluginManifest,
    PluginRegistry,
)
from antinode_norma.execution.parallel import ParallelExecutor
from antinode_norma.gates.runner import GateRunner
from antinode_norma.governance.approval import ApprovalGate
from antinode_norma.governance.audit import AuditLog
from antinode_norma.ingest_structured.csv import CSVIngester
from antinode_norma.server.api import app


def test_cross_track_end_to_end_regression(tmp_path):
    # 1. Track A: Ingestion & NormaAgent Generation
    csv_file = tmp_path / "test_suite.csv"
    csv_file.write_text(
        "ID,Summary,As a,I want to,So that,Acceptance Criteria\n"
        "REG-101,Account Password Reset,registered user,reset my password,regain access,Email sent with reset link\n",
        encoding="utf-8",
    )

    ingester = CSVIngester()
    cases = ingester.ingest(str(csv_file))
    assert len(cases) == 1
    assert cases[0].id == "REG-101"

    def mock_llm(prompt: str) -> str:
        return """
@REG-101
Feature: Account Password Reset
  Scenario: Send password reset email
    Given the user is on login page
    When the user clicks forgot password
    Then password reset email is sent
"""

    agent = NormaAgent(llm_callable=mock_llm)
    gherkin_text, verdict, attempts = agent.generate_feature_with_repair(cases)
    assert attempts == 1
    assert verdict.hard_pass is True

    # 2. Quality Gates Evaluation (Q0-Q10)
    from antinode_norma.gates.types import GateContext

    ctx = GateContext(gherkin_text=gherkin_text, test_cases=cases)
    runner = GateRunner()
    eval_verdict = runner.evaluate(ctx)
    assert eval_verdict.hard_pass is True
    assert eval_verdict.soft_score >= 0.85

    # 3. Track A: Governance & Audit Trail
    audit = AuditLog(log_path=tmp_path / "audit.jsonl")
    audit.record_user_action(
        user_id="user_admin",
        action="feature:generate",
        resource="REG-101",
        result="success",
        ip="127.0.0.1",
        user_agent="PytestRunner/1.0",
        payload={"gherkin_len": len(gherkin_text)},
    )
    assert audit.verify_integrity() is True

    approval_gate = ApprovalGate(audit_log=audit)
    req = approval_gate.submit_request(feature_id="REG-101", gherkin_text=gherkin_text, requested_by="user_admin")
    approved_req = approval_gate.approve(request_id=req.id, reviewer="qa_lead", reason="Fully validated")
    assert approved_req.status.value == "APPROVED"

    # 4. Track B: Parallel Execution Engine
    executor = ParallelExecutor(max_workers=2)
    tasks = [{"id": f"t{i}", "name": f"test_{i}"} for i in range(3)]
    exec_result = executor.execute_parallel(tasks, lambda t: f"Passed: {t['name']}")
    assert exec_result.passed_count == 3

    # 5. Track C: REST API & Permission Verification
    client = TestClient(app, headers={"X-User-ID": "admin_user"})

    health_res = client.get("/health")
    assert health_res.status_code == 200

    analytics_res = client.get("/api/analytics/summary")
    assert analytics_res.status_code == 200

    # 6. Convergent Track: Ecosystem & Collaboration
    registry = PluginRegistry()
    lifecycle = PluginLifecycleManager(registry)

    manifest = PluginManifest(name="regression-plugin", permissions=["read:features"])
    lifecycle.load_plugin(manifest, enabled=True)

    hook_runner = PluginHookRunner(registry)
    hook_events = []
    hook_runner.register_hook(
        hook_name="on_regression_complete",
        plugin_name="regression-plugin",
        callback=lambda msg: hook_events.append(msg),
        required_permission="read:features",
    )
    hook_runner.trigger_hook("on_regression_complete", msg="Regression Passed")
    assert hook_events == ["Regression Passed"]

    # Collaboration comment & notification
    comment_store = CommentStore()
    c = comment_store.add_comment("REG-101", "user_admin", "Cross track regression complete @qa_lead")
    assert c.mentions == ["qa_lead"]

    notif_mgr = NotificationManager()
    notif_res = notif_mgr.send_notification(
        Notification(
            event_type="regression_complete",
            title="Regression Test Passed",
            message=c.text,
            channel="email",
            recipient="qa_lead@norma.local",
        )
    )
    assert notif_res["status"] == "sent"

    # Collector summary
    collector = AnalyticsCollector(approval_gate=approval_gate, audit_log=audit)
    summary = collector.collect_summary(feature_count=1)
    assert summary.approved_count == 1
