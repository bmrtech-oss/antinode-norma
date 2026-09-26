from fastapi.testclient import TestClient
from antinode_norma.auth.middleware import get_current_user
from antinode_norma.auth.models import Role, User
from antinode_norma.server.api import app

client = TestClient(app)


def test_get_dashboard_summary_unauthenticated():
    app.dependency_overrides[get_current_user] = lambda: None
    try:
        response = client.get("/api/dashboard")
        assert response.status_code == 401
    finally:
        app.dependency_overrides = {}


def test_get_dashboard_summary_authenticated():
    user = User(username="dashboard_user", email="user@norma.local", roles=[Role.VIEWER])
    app.dependency_overrides[get_current_user] = lambda: user

    try:
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
    finally:
        app.dependency_overrides = {}
