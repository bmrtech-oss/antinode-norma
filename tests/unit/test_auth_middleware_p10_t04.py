"""Unit tests for Phase 10 Task P10-T04: Permission Middleware & Route Security."""

from fastapi import FastAPI, Depends, Request
from fastapi.testclient import TestClient

from antinode_norma.auth.models import Role, User
from antinode_norma.auth.roles import ADMIN_WRITE, FEATURE_READ, FEATURE_WRITE
from antinode_norma.auth.middleware import requires_permission


def test_middleware_unauthenticated_returns_401():
    app_unauth = FastAPI()

    @app_unauth.get("/read", dependencies=[Depends(requires_permission(FEATURE_READ))])
    async def read_route():
        return {"status": "ok"}

    client = TestClient(app_unauth)
    resp = client.get("/read")
    assert resp.status_code == 401
    assert "Authentication required" in resp.json()["detail"]


def test_middleware_inactive_user_returns_401():
    app_inactive = FastAPI()

    @app_inactive.middleware("http")
    async def set_inactive_user(request: Request, call_next):
        request.state.user = User(
            username="inactive",
            email="inactive@norma.local",
            roles=[Role.ADMIN],
            is_active=False,
        )
        return await call_next(request)

    @app_inactive.get("/read", dependencies=[Depends(requires_permission(FEATURE_READ))])
    async def read_inactive():
        return {"status": "ok"}

    client = TestClient(app_inactive)
    resp = client.get("/read")
    assert resp.status_code == 401


def test_middleware_insufficient_permissions_returns_403():
    app_viewer = FastAPI()

    @app_viewer.middleware("http")
    async def set_viewer_user(request: Request, call_next):
        request.state.user = User(
            username="viewer",
            email="viewer@norma.local",
            roles=[Role.VIEWER],
        )
        return await call_next(request)

    @app_viewer.post("/write", dependencies=[Depends(requires_permission(FEATURE_WRITE))])
    async def viewer_write():
        return {"status": "ok"}

    client = TestClient(app_viewer)
    resp = client.post("/write")
    assert resp.status_code == 403
    assert "Permission 'feature:write' required" in resp.json()["detail"]


def test_middleware_authorized_user_returns_200():
    app_admin = FastAPI()

    @app_admin.middleware("http")
    async def set_admin_user(request: Request, call_next):
        request.state.user = User(
            username="admin",
            email="admin@norma.local",
            roles=[Role.ADMIN],
        )
        return await call_next(request)

    @app_admin.get("/admin", dependencies=[Depends(requires_permission(ADMIN_WRITE))])
    async def admin_ok():
        return {"status": "ok"}

    client = TestClient(app_admin)
    resp = client.get("/admin")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
