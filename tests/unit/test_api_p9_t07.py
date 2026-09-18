from fastapi.testclient import TestClient
from antinode_norma.server.api import app

client = TestClient(app)


def test_get_dashboard_summary():
    response = client.get("/api/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    summary = data["summary"]
    assert "total_features" in summary
    assert "total_approvals" in summary
    assert "pending_approvals" in summary
    assert "total_audit_events" in summary
    assert "quality_gate_pass_rate" in summary
    assert summary["system_status"] == "operational"
