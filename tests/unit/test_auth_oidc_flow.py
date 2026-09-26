"""Deterministic OIDC authorization-code exchange and validation tests."""

from datetime import datetime, timedelta, timezone
import json
import urllib.parse

import httpx
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
import pytest
from fastapi.testclient import TestClient

from antinode_norma.auth.oidc import (
    OIDCConfig,
    OIDCProviderError,
    OIDCTransactionStore,
    exchange_code_and_validate_id_token,
)
from antinode_norma import database
from antinode_norma.server.api import app
from antinode_norma.server.routes import auth as auth_routes


ISSUER = "https://identity.example.test"
CLIENT_ID = "norma-web"
DISCOVERY_URL = f"{ISSUER}/.well-known/openid-configuration"
JWKS_URL = f"{ISSUER}/jwks"


def _provider_fixture(
    claim_overrides=None,
    *,
    token_status=200,
    expected_verifier="server-held-verifier",
    invalid_signature=False,
):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    signing_key = (
        rsa.generate_private_key(public_exponent=65537, key_size=2048)
        if invalid_signature
        else private_key
    )
    public_jwk = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(private_key.public_key()))
    public_jwk.update({"kid": "test-key", "use": "sig", "alg": "RS256"})
    nonce_state = {"value": None}

    def handler(request):
        if request.url.path.endswith("/.well-known/openid-configuration"):
            return httpx.Response(
                200,
                json={
                    "issuer": ISSUER,
                    "authorization_endpoint": f"{ISSUER}/authorize",
                    "token_endpoint": f"{ISSUER}/token",
                    "jwks_uri": JWKS_URL,
                },
            )
        if request.url.path == "/token":
            if token_status != 200:
                return httpx.Response(token_status, json={"error": "invalid_grant"})
            form = urllib.parse.parse_qs(request.content.decode("utf-8"))
            assert form["grant_type"] == ["authorization_code"]
            assert form["code"] == ["authorization-code"]
            verifier = form["code_verifier"][0]
            if expected_verifier is not None:
                assert verifier == expected_verifier
            else:
                assert 43 <= len(verifier) <= 128
            assert request.headers.get("authorization", "").startswith("Basic ")
            now = datetime.now(timezone.utc)
            claims = {
                "iss": ISSUER,
                "sub": "subject-123",
                "aud": CLIENT_ID,
                "iat": int(now.timestamp()),
                "exp": int((now + timedelta(minutes=5)).timestamp()),
                "nonce": nonce_state["value"],
                "email": "person@example.test",
                "preferred_username": "person",
                "name": "Example Person",
            }
            claims.update(claim_overrides or {})
            signed_token = jwt.encode(
                claims,
                signing_key,
                algorithm="RS256",
                headers={"kid": "test-key"},
            )
            return httpx.Response(200, json={"id_token": signed_token})
        if request.url == httpx.URL(JWKS_URL):
            return httpx.Response(200, json={"keys": [public_jwk]})
        return httpx.Response(404)

    return httpx.MockTransport(handler), nonce_state


def _config():
    return OIDCConfig(
        issuer=ISSUER,
        client_id=CLIENT_ID,
        client_secret="test-secret",
        redirect_uri="http://localhost:8000/api/auth/oidc/callback",
    )


@pytest.mark.asyncio
async def test_exchange_and_validate_signed_id_token():
    transport, nonce_state = _provider_fixture()
    nonce_state["value"] = "expected-nonce"
    async with httpx.AsyncClient(transport=transport) as client:
        claims = await exchange_code_and_validate_id_token(
            _config(),
            code="authorization-code",
            verifier="server-held-verifier",
            nonce="expected-nonce",
            client=client,
        )

    assert claims["sub"] == "subject-123"
    assert claims["email"] == "person@example.test"


@pytest.mark.parametrize(
    ("overrides", "expected_message"),
    [
        ({"nonce": "wrong-nonce"}, "nonce validation failed"),
        ({"iss": "https://attacker.example.test"}, "ID token validation failed"),
        ({"aud": "another-client"}, "ID token validation failed"),
        ({"exp": 1}, "ID token validation failed"),
    ],
)
@pytest.mark.asyncio
async def test_exchange_rejects_invalid_id_token_claims(overrides, expected_message):
    transport, nonce_state = _provider_fixture(overrides)
    nonce_state["value"] = "expected-nonce"
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(OIDCProviderError, match=expected_message):
            await exchange_code_and_validate_id_token(
                _config(),
                code="authorization-code",
                verifier="server-held-verifier",
                nonce="expected-nonce",
                client=client,
            )


@pytest.mark.asyncio
async def test_exchange_rejects_id_token_with_invalid_signature():
    transport, nonce_state = _provider_fixture(invalid_signature=True)
    nonce_state["value"] = "expected-nonce"
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(OIDCProviderError, match="ID token validation failed"):
            await exchange_code_and_validate_id_token(
                _config(),
                code="authorization-code",
                verifier="server-held-verifier",
                nonce="expected-nonce",
                client=client,
            )


@pytest.mark.asyncio
async def test_exchange_rejects_provider_token_exchange_failure():
    transport, _ = _provider_fixture(token_status=400)
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(OIDCProviderError, match="code exchange failed"):
            await exchange_code_and_validate_id_token(
                _config(),
                code="authorization-code",
                verifier="server-held-verifier",
                nonce="expected-nonce",
                client=client,
            )


def test_oidc_transaction_is_one_time_and_expires(monkeypatch):
    import antinode_norma.auth.oidc as oidc_module

    clock = {"now": 100.0}
    monkeypatch.setattr(oidc_module.time, "monotonic", lambda: clock["now"])
    store = OIDCTransactionStore(ttl_seconds=30)
    store.create("state-once", verifier="verifier", nonce="nonce", config=_config())

    assert store.consume("state-once")["nonce"] == "nonce"
    assert store.consume("state-once") is None

    store.create("state-expired", verifier="verifier", nonce="nonce", config=_config())
    clock["now"] = 131.0
    assert store.consume("state-expired") is None


def test_oidc_api_flow_keeps_verifier_server_side_and_rejects_replay(monkeypatch, tmp_path):
    monkeypatch.setenv("NORMA_AUTH_MODE", "oidc")
    monkeypatch.setenv("NORMA_AUTH_ALLOW_IDENTITY_HEADERS", "false")
    monkeypatch.setenv("NORMA_OIDC_ISSUER", ISSUER)
    monkeypatch.delenv("NORMA_OIDC_DISCOVERY_URL", raising=False)
    monkeypatch.setenv("NORMA_OIDC_CLIENT_ID", CLIENT_ID)
    monkeypatch.setenv("NORMA_OIDC_CLIENT_SECRET", "test-secret")
    monkeypatch.setenv("NORMA_OIDC_REDIRECT_URI", "http://localhost:8000/api/auth/oidc/callback")
    monkeypatch.setenv("NORMA_AUTH_ALLOWED_ORIGINS", "http://localhost:3000")
    database_url = f"sqlite:///{tmp_path / 'auth-sessions.db'}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    database.migrate(database_url)
    transport, nonce_state = _provider_fixture(expected_verifier=None)
    async_client_class = httpx.AsyncClient

    def create_client(*, timeout):
        return async_client_class(transport=transport, timeout=timeout)

    monkeypatch.setattr(auth_routes.httpx, "AsyncClient", create_client)
    with TestClient(app) as client:
        login_response = client.get(
            "/api/auth/oidc/login",
            params={"return_to": "/approvals?filter=pending"},
        )
        assert login_response.status_code == 200
        login_data = login_response.json()
        assert "code_verifier" not in login_data

        auth_params = urllib.parse.parse_qs(
            urllib.parse.urlparse(login_data["authorization_url"]).query
        )
        nonce_state["value"] = auth_params["nonce"][0]
        assert auth_params["code_challenge_method"] == ["S256"]

        callback = client.get(
            "/api/auth/oidc/callback",
            params={"code": "authorization-code", "state": auth_params["state"][0]},
            follow_redirects=False,
        )
        assert callback.status_code == 303
        assert callback.headers["location"] == (
            "http://localhost:3000/approvals?filter=pending"
        )
        assert "httponly" in callback.headers["set-cookie"].lower()
        raw_session_token = client.cookies.get(auth_routes.SESSION_COOKIE_NAME)
        assert raw_session_token

        me_response = client.get("/api/auth/me")
        assert me_response.status_code == 200
        me_data = me_response.json()
        assert me_data["user"]["id"] == "subject-123"
        assert me_data["permissions"] == ["audit:read", "feature:read"]
        assert me_data["session_expires_at"]

        stored = database.execute(database_url, "SELECT session_token_hash FROM auth_sessions")
        assert stored and stored[0][0] != raw_session_token

        replay = client.get(
            "/api/auth/oidc/callback",
            params={"code": "authorization-code", "state": auth_params["state"][0]},
        )
        assert replay.status_code == 400

        csrf_token = client.cookies.get("norma_csrf")
        logout = client.post(
            "/api/auth/logout",
            headers={"Origin": "http://localhost:3000", "X-CSRF-Token": csrf_token},
        )
        assert logout.status_code == 200
        assert logout.json() == {"status": "logged_out"}
        assert client.get("/api/auth/me").status_code == 401

        revoked_at = database.execute(database_url, "SELECT revoked_at FROM auth_sessions")
        assert revoked_at[0][0] is not None


def test_oidc_login_rejects_external_return_origin(monkeypatch):
    monkeypatch.setenv("NORMA_AUTH_MODE", "oidc")
    monkeypatch.setenv("NORMA_AUTH_ALLOW_IDENTITY_HEADERS", "false")
    monkeypatch.setenv("NORMA_OIDC_ISSUER", ISSUER)
    monkeypatch.delenv("NORMA_OIDC_DISCOVERY_URL", raising=False)
    monkeypatch.setenv("NORMA_OIDC_CLIENT_ID", CLIENT_ID)
    monkeypatch.setenv("NORMA_OIDC_CLIENT_SECRET", "test-secret")
    monkeypatch.setenv("NORMA_OIDC_REDIRECT_URI", "http://localhost:8000/api/auth/oidc/callback")
    monkeypatch.setenv("NORMA_AUTH_ALLOWED_ORIGINS", "http://localhost:3000")

    with TestClient(app) as client:
        response = client.get(
            "/api/auth/oidc/login",
            params={"return_to": "https://attacker.example.test/steal"},
        )

    assert response.status_code == 400