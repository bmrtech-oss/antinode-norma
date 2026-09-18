"""Unit tests for Phase 10 Task P10-T05: User Action Audit Logging."""

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from antinode_norma.auth.middleware import log_user_action
from antinode_norma.auth.models import Role, User
from antinode_norma.governance.audit import AuditLog
from antinode_norma.server.routes.audit import audit_log, router as audit_router


def test_audit_log_record_user_action():
    log = AuditLog()
    initial_count = len(log.records)

    record = log.record_user_action(
        user_id="user_123",
        action="feature:approve",
        resource="feature:login.feature",
        result="success",
        ip="192.168.1.50",
        user_agent="TestAgent/1.0",
        payload={"comment": "Approved by QA"},
    )

    assert len(log.records) == initial_count + 1
    assert record.actor == "user_123"
    assert record.action == "feature:approve"
    assert record.resource == "feature:login.feature"
    assert record.payload["user_id"] == "user_123"
    assert record.payload["result"] == "success"
    assert record.payload["ip"] == "192.168.1.50"
    assert record.payload["user_agent"] == "TestAgent/1.0"
    assert record.payload["comment"] == "Approved by QA"
    assert log.verify_integrity() is True


def test_log_user_action_helper():
    app = FastAPI()

    @app.post("/test-action")
    async def test_endpoint(request: Request):
        user = User(id="usr_admin", username="admin", email="admin@norma.local", roles=[Role.ADMIN])
        log_user_action(
            request=request,
            user=user,
            action="feature:create",
            resource="feature:checkout.feature",
            result="success",
            payload={"source": "unit_test"},
        )
        return {"status": "ok"}

    client = TestClient(app)
    resp = client.post("/test-action", headers={"User-Agent": "PytestClient/2.0"})
    assert resp.status_code == 200

    latest_record = audit_log.records[-1]
    assert latest_record.actor == "usr_admin"
    assert latest_record.action == "feature:create"
    assert latest_record.payload["user_agent"] == "PytestClient/2.0"
    assert latest_record.payload["source"] == "unit_test"


def test_audit_route_permissions():
    app_audit = FastAPI()
    app_audit.include_router(audit_router)

    client = TestClient(app_audit)

    # Unauthenticated -> 401
    unauth_resp = client.get("/api/audit")
    assert unauth_resp.status_code == 401

    # Viewer/Admin authenticated -> 200
    auth_resp = client.get("/api/audit", headers={"X-User-ID": "admin_user"})
    assert auth_resp.status_code == 200
    assert isinstance(auth_resp.json(), list)

    verify_resp = client.get("/api/audit/verify", headers={"X-User-ID": "admin_user"})
    assert verify_resp.status_code == 200
    assert verify_resp.json()["is_valid"] is True
