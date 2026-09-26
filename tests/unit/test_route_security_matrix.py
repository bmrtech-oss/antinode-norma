"""Focused unit tests for AUTH-0-T06: Protected Route Security Matrix."""

from fastapi import HTTPException
from fastapi.testclient import TestClient

from antinode_norma.auth.middleware import ensure_resource_owner, get_current_user
from antinode_norma.auth.models import Role, User
from antinode_norma.server.api import app
from antinode_norma.server.routes.audit import audit_log

client = TestClient(app)


def test_anonymous_access_returns_401_for_all_protected_routes():
    app.dependency_overrides[get_current_user] = lambda: None
    try:
        protected_get_routes = [
            "/api/dashboard",
            "/api/traceability",
            "/api/features",
            "/api/analytics/summary",
            "/api/comments",
            "/api/audit",
            "/api/audit/verify",
            "/api/approvals",
            "/api/admin/settings",
            "/api/generation-jobs",
        ]
        for route in protected_get_routes:
            res = client.get(route)
            assert res.status_code == 401, f"Expected 401 for anonymous GET {route}, got {res.status_code}"

        protected_post_routes = [
            ("/api/comments", {"feature_id": "F1", "text": "hello"}),
            ("/api/notifications/send", {"event_type": "test", "recipient": "user@norma.local", "channel": "email", "title": "test", "message": "msg"}),
            ("/api/approvals", {"feature_id": "F1"}),
        ]
        for route, body in protected_post_routes:
            res = client.post(route, json=body)
            assert res.status_code == 401, f"Expected 401 for anonymous POST {route}, got {res.status_code}"
    finally:
        app.dependency_overrides = {}


def test_viewer_role_route_matrix():
    viewer = User(id="viewer-1", username="viewer", email="v@norma.local", roles=[Role.VIEWER])
    app.dependency_overrides[get_current_user] = lambda: viewer

    try:
        # Viewer can read features, dashboard, traceability, analytics, comments, audit, approvals
        assert client.get("/api/dashboard").status_code == 200
        assert client.get("/api/traceability").status_code == 200
        assert client.get("/api/features").status_code == 200
        assert client.get("/api/analytics/summary").status_code == 200
        assert client.get("/api/comments").status_code == 200
        assert client.get("/api/audit").status_code == 200
        assert client.get("/api/audit/verify").status_code == 200
        assert client.get("/api/approvals").status_code == 200

        # Viewer cannot create approvals (requires approval:action) -> 403
        res_appr = client.post("/api/approvals", json={"feature_id": "F1"})
        assert res_appr.status_code == 403

        # Viewer cannot access admin settings -> 403
        res_admin_get = client.get("/api/admin/settings")
        assert res_admin_get.status_code == 403

        res_admin_put = client.put("/api/admin/settings", json={"app_name": "New Name"})
        assert res_admin_put.status_code == 403
    finally:
        app.dependency_overrides = {}


def test_generator_role_route_matrix():
    generator = User(id="gen-1", username="generator", email="g@norma.local", roles=[Role.GENERATOR])
    app.dependency_overrides[get_current_user] = lambda: generator

    try:
        # Generator can read
        assert client.get("/api/dashboard").status_code == 200

        # Generator can write comments and notifications
        res_comment = client.post("/api/comments", json={"feature_id": "F1", "text": "gen comment"})
        assert res_comment.status_code == 200

        # Generator cannot create approvals -> 403
        res_appr = client.post("/api/approvals", json={"feature_id": "F1"})
        assert res_appr.status_code == 403

        # Generator cannot access admin settings -> 403
        assert client.get("/api/admin/settings").status_code == 403
    finally:
        app.dependency_overrides = {}


def test_reviewer_role_route_matrix():
    reviewer = User(id="rev-1", username="reviewer", email="r@norma.local", roles=[Role.REVIEWER])
    app.dependency_overrides[get_current_user] = lambda: reviewer

    try:
        # Reviewer can read
        assert client.get("/api/dashboard").status_code == 200

        # Reviewer can create approvals
        res_appr = client.post("/api/approvals", json={"feature_id": "F1"})
        assert res_appr.status_code == 200

        # Reviewer cannot access admin settings -> 403
        assert client.get("/api/admin/settings").status_code == 403
    finally:
        app.dependency_overrides = {}


def test_admin_role_route_matrix():
    admin = User(id="admin-1", username="admin", email="a@norma.local", roles=[Role.ADMIN])
    app.dependency_overrides[get_current_user] = lambda: admin

    try:
        # Admin can access admin settings
        res_admin_get = client.get("/api/admin/settings")
        assert res_admin_get.status_code == 200

        # Admin can perform approvals
        res_appr = client.post("/api/approvals", json={"feature_id": "F2"})
        assert res_appr.status_code == 200
    finally:
        app.dependency_overrides = {}


def test_resource_ownership_enforcement():
    user1 = User(id="u1", username="u1", email="u1@norma.local", tenant_id="tenant-A", roles=[Role.VIEWER])
    user2 = User(id="u2", username="u2", email="u2@norma.local", tenant_id="tenant-B", roles=[Role.VIEWER])
    admin = User(id="admin", username="admin", email="admin@norma.local", tenant_id="tenant-A", roles=[Role.ADMIN])

    resource = {"id": "res-1", "owner_id": "u1", "tenant_id": "tenant-A"}

    # Owner in same tenant -> passes
    ensure_resource_owner(user1, resource)

    # Admin in different owner but same tenant -> passes
    ensure_resource_owner(admin, resource)

    # Different tenant -> 404
    try:
        ensure_resource_owner(user2, resource)
        assert False, "Should have raised 404 for tenant mismatch"
    except HTTPException as exc:
        assert exc.status_code == 404

    # Different owner, same tenant, non-admin -> 404
    other_user_same_tenant = User(id="u3", username="u3", email="u3@norma.local", tenant_id="tenant-A", roles=[Role.VIEWER])
    try:
        ensure_resource_owner(other_user_same_tenant, resource)
        assert False, "Should have raised 404 for owner mismatch"
    except HTTPException as exc:
        assert exc.status_code == 404


def test_actor_attribution_in_audit_log():
    user = User(id="user-777", username="user777", email="user777@norma.local", tenant_id="tenant-XYZ", roles=[Role.ADMIN])
    app.dependency_overrides[get_current_user] = lambda: user

    try:
        initial_records = len(audit_log.records)
        res = client.put("/api/admin/settings", json={"app_name": "Audit Test Platform"})
        assert res.status_code == 200

        assert len(audit_log.records) > initial_records
        latest = audit_log.records[-1]
        assert latest.actor == "user-777"
        assert latest.action == "admin:settings_update"
        assert latest.payload.get("tenant_id") == "tenant-XYZ"
    finally:
        app.dependency_overrides = {}
