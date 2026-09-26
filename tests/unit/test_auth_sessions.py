"""Persistence tests for durable browser authentication sessions."""

from datetime import datetime, timedelta, timezone
import hashlib

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from fastapi.middleware.cors import CORSMiddleware

from antinode_norma import database
from antinode_norma.auth.config import AuthSettings
from antinode_norma.auth.middleware import AuthCSRFMiddleware, requires_permission
from antinode_norma.auth.roles import FEATURE_READ
from antinode_norma.server.api import cors_options_for_auth


def _session(
    token_hash,
    *,
    issuer="https://identity.example.test",
    subject="user-1",
    sid="sid-1",
    expires=None,
):
    now = datetime.now(timezone.utc)
    return {
        "session_token_hash": token_hash,
        "user_id": subject,
        "user": {
            "id": subject,
            "username": "user",
            "email": "user@example.test",
            "roles": ["viewer"],
        },
        "issuer": issuer,
        "subject": subject,
        "idp_sid": sid,
        "expires_at": (expires or now + timedelta(hours=1)).isoformat(),
        "created_at": now.isoformat(),
    }


def test_auth_session_is_durable_and_revocable_across_database_connections(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'sessions.db'}"
    database.migrate(database_url)
    database.save_auth_session(database_url, _session("hashed-token-value"))

    loaded = database.load_auth_session(database_url, "hashed-token-value")
    assert loaded["user"]["id"] == "user-1"
    assert loaded["issuer"] == "https://identity.example.test"
    assert loaded["idp_sid"] == "sid-1"
    assert database.revoke_auth_session(database_url, "hashed-token-value") is True
    assert database.load_auth_session(database_url, "hashed-token-value") is None


def test_expired_auth_session_is_not_loaded_and_is_revoked(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'expired-sessions.db'}"
    database.migrate(database_url)
    now = datetime.now(timezone.utc)
    database.save_auth_session(
        database_url,
        _session("expired-token", expires=now - timedelta(seconds=1)),
    )

    assert database.load_auth_session(database_url, "expired-token", now=now) is None
    row = database.execute(
        database_url,
        "SELECT revoked_at FROM auth_sessions WHERE session_token_hash = ?",
        ("expired-token",),
    )
    assert row[0][0] is not None


def test_upstream_identity_revocation_is_scoped_by_issuer_and_session(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'revoked-sessions.db'}"
    database.migrate(database_url)
    database.save_auth_session(database_url, _session("same-user-sid-a", sid="sid-a"))
    database.save_auth_session(database_url, _session("same-user-sid-b", sid="sid-b"))
    database.save_auth_session(
        database_url,
        _session("different-issuer", issuer="https://other.example.test", sid="sid-a"),
    )

    count = database.revoke_auth_sessions_for_identity(
        database_url,
        issuer="https://identity.example.test",
        idp_sid="sid-a",
    )

    assert count == 1
    assert database.load_auth_session(database_url, "same-user-sid-a") is None
    assert database.load_auth_session(database_url, "same-user-sid-b") is not None
    assert database.load_auth_session(database_url, "different-issuer") is not None


def test_protected_route_uses_durable_session_cookie_and_fails_closed(monkeypatch, tmp_path):
    database_url = f"sqlite:///{tmp_path / 'protected-route.db'}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    database.migrate(database_url)
    raw_token = "browser-session-secret"
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    database.save_auth_session(database_url, _session(token_hash))

    app = FastAPI()

    @app.get("/protected", dependencies=[Depends(requires_permission(FEATURE_READ))])
    async def protected():
        return {"ok": True}

    with TestClient(app) as client:
        client.cookies.set("norma_session", raw_token)
        authorized = client.get("/protected")
        assert authorized.status_code == 200

        client.cookies.set("norma_session", "invalid")
        invalid_cookie_with_spoofed_header = client.get(
            "/protected",
            headers={"X-User-ID": "admin"},
        )
        assert invalid_cookie_with_spoofed_header.status_code == 401


def test_oidc_cors_uses_exact_origins_and_credentials():
    settings = AuthSettings.from_environment(
        {
            "NORMA_ENVIRONMENT": "production",
            "NORMA_AUTH_MODE": "oidc",
            "NORMA_OIDC_ISSUER": "https://identity.example.test",
            "NORMA_OIDC_CLIENT_ID": "norma-web",
            "NORMA_OIDC_CLIENT_SECRET": "secret",
            "NORMA_OIDC_REDIRECT_URI": "https://api.example.test/api/auth/oidc/callback",
            "NORMA_AUTH_ALLOWED_ORIGINS": "https://ui.example.test",
        }
    )
    options = cors_options_for_auth(settings)
    cors_app = FastAPI()
    cors_app.add_middleware(CORSMiddleware, **options)

    @cors_app.post("/mutation")
    async def mutate():
        return {"ok": True}

    with TestClient(cors_app) as client:
        preflight = client.options(
            "/mutation",
            headers={
                "Origin": "https://ui.example.test",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type,x-csrf-token",
            },
        )
        assert preflight.status_code == 200
        assert preflight.headers["access-control-allow-origin"] == "https://ui.example.test"
        assert preflight.headers["access-control-allow-credentials"] == "true"

        untrusted_preflight = client.options(
            "/mutation",
            headers={
                "Origin": "https://attacker.example.test",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert untrusted_preflight.status_code == 400


def test_csrf_middleware_requires_matching_token_and_allowed_origin(monkeypatch, tmp_path):
    database_url = f"sqlite:///{tmp_path / 'csrf-sessions.db'}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("NORMA_ENVIRONMENT", "development")
    monkeypatch.setenv("NORMA_AUTH_MODE", "oidc")
    monkeypatch.setenv("NORMA_AUTH_ALLOW_IDENTITY_HEADERS", "false")
    monkeypatch.setenv("NORMA_OIDC_ISSUER", "https://identity.example.test")
    monkeypatch.setenv("NORMA_OIDC_CLIENT_ID", "norma-web")
    monkeypatch.setenv("NORMA_OIDC_CLIENT_SECRET", "secret")
    monkeypatch.setenv("NORMA_OIDC_REDIRECT_URI", "http://api.example.test/api/auth/oidc/callback")
    monkeypatch.setenv("NORMA_AUTH_ALLOWED_ORIGINS", "http://ui.example.test")
    database.migrate(database_url)
    raw_session = "csrf-bound-session"
    raw_csrf = "session-bound-csrf-token"
    session_hash = hashlib.sha256(raw_session.encode("utf-8")).hexdigest()
    session = _session(session_hash)
    session["user"]["roles"] = ["generator"]
    session["csrf_token_hash"] = hashlib.sha256(raw_csrf.encode("utf-8")).hexdigest()
    database.save_auth_session(database_url, session)

    csrf_app = FastAPI()
    csrf_app.add_middleware(AuthCSRFMiddleware)

    @csrf_app.post("/mutation", dependencies=[Depends(requires_permission(FEATURE_READ))])
    async def mutate():
        return {"ok": True}

    with TestClient(csrf_app) as client:
        client.cookies.set("norma_session", raw_session)
        client.cookies.set("norma_csrf", raw_csrf)
        allowed = client.post(
            "/mutation",
            headers={"Origin": "http://ui.example.test", "X-CSRF-Token": raw_csrf},
        )
        assert allowed.status_code == 200

        missing_header = client.post("/mutation", headers={"Origin": "http://ui.example.test"})
        assert missing_header.status_code == 403

        wrong_origin = client.post(
            "/mutation",
            headers={"Origin": "http://attacker.example.test", "X-CSRF-Token": raw_csrf},
        )
        assert wrong_origin.status_code == 403
