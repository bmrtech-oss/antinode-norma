"""Unit tests for Phase 10 Task P10-T02: OIDC Integration & API Endpoints."""

import urllib.parse
from fastapi.testclient import TestClient

from antinode_norma.auth.models import Role
from antinode_norma.auth.oidc import (
    OIDCConfig,
    build_authorization_url,
    generate_pkce_pair,
    map_claims_to_user,
)
from antinode_norma.server.api import app

client = TestClient(app)


def test_oidc_config_defaults():
    config = OIDCConfig()
    assert config.issuer == "https://auth.example.com"
    assert config.client_id == "norma-client"
    assert "openid" in config.scopes
    assert "profile" in config.scopes
    assert config.get_authorization_endpoint().endswith("/protocol/openid-connect/auth")
    assert config.get_token_endpoint().endswith("/protocol/openid-connect/token")


def test_generate_pkce_pair():
    verifier, challenge = generate_pkce_pair()
    assert len(verifier) >= 43
    assert len(challenge) >= 43
    assert verifier != challenge


def test_build_authorization_url():
    config = OIDCConfig()
    verifier, challenge = generate_pkce_pair()
    url = build_authorization_url(config, state="test_state_123", code_challenge=challenge)

    assert url.startswith("https://auth.example.com")
    parsed = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(parsed.query)

    assert params["client_id"] == ["norma-client"]
    assert params["response_type"] == ["code"]
    assert params["state"] == ["test_state_123"]
    assert params["code_challenge"] == [challenge]
    assert params["code_challenge_method"] == ["S256"]


def test_map_claims_to_user():
    claims = {
        "sub": "auth0|123456",
        "email": "alice@example.com",
        "preferred_username": "alice_w",
        "name": "Alice Wonder",
    }
    user = map_claims_to_user(claims, roles=[Role.REVIEWER])

    assert user.id == "auth0|123456"
    assert user.email == "alice@example.com"
    assert user.username == "alice_w"
    assert user.display_name == "Alice Wonder"
    assert user.roles == [Role.REVIEWER]


def test_oidc_api_flow():
    # 1. Login initiate
    login_resp = client.get("/api/auth/oidc/login")
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    assert "authorization_url" in login_data
    assert "state" in login_data
    assert "code_verifier" in login_data

    # 2. Callback token exchange
    callback_resp = client.post(
        "/api/auth/oidc/callback",
        json={
            "code": "test_auth_code_987",
            "state": login_data["state"],
            "code_verifier": login_data["code_verifier"],
        },
    )
    assert callback_resp.status_code == 200
    user_data = callback_resp.json()
    assert user_data["username"] == "oidc_user"
    assert user_data["email"] == "oidc.user@example.com"

    # 3. Get Me
    me_resp = client.get(f"/api/auth/oidc/me?user_id={user_data['id']}")
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["id"] == user_data["id"]
    assert me_data["username"] == "oidc_user"
