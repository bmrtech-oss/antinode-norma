from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from antinode_norma.auth.models import Role, User
from antinode_norma.server.api import app


def _client_with_user(user: User | None) -> TestClient:
    test_app = FastAPI()

    @test_app.middleware("http")
    async def inject_user(request: Request, call_next):
        if user is not None:
            request.state.user = user
        return await call_next(request)

    test_app.include_router(app.router)
    return TestClient(test_app)


def test_get_dashboard_summary_unauthenticated():
    client = _client_with_user(None)
    response = client.get("/api/dashboard")
    assert response.status_code == 401


def test_get_dashboard_summary_authenticated():
    user = User(username="dashboard_user", email="user@norma.local", roles=[Role.VIEWER])
    client = _client_with_user(user)

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
