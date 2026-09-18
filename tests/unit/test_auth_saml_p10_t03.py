"""Unit tests for Phase 10 Task P10-T03: SAML 2.0 Integration & Feature Flag Gating."""

import base64
from fastapi.testclient import TestClient

from antinode_norma.auth.saml import (
    SAMLConfig,
    build_authn_request,
    generate_sp_metadata,
    parse_saml_response_claims,
)
from antinode_norma.server.api import app

client = TestClient(app)


def test_saml_config_defaults():
    config = SAMLConfig()
    assert config.entity_id == "https://idp.example.com/saml/metadata"
    assert config.sso_url == "https://idp.example.com/saml/sso"
    assert config.sp_entity_id == "https://norma.example.com/saml/metadata"
    assert config.sp_acs_url == "http://localhost:8000/api/auth/saml/acs"


def test_build_authn_request():
    config = SAMLConfig()
    url = build_authn_request(config, issue_instant="2026-09-17T12:00:00Z")
    assert url.startswith("https://idp.example.com/saml/sso?SAMLRequest=")


def test_generate_sp_metadata():
    config = SAMLConfig()
    metadata_xml = generate_sp_metadata(config)
    assert '<md:EntityDescriptor' in metadata_xml
    assert 'entityID="https://norma.example.com/saml/metadata"' in metadata_xml
    assert 'Location="http://localhost:8000/api/auth/saml/acs"' in metadata_xml


def test_parse_saml_response_claims():
    fake_response = '<saml:Response xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion"><saml:NameID>user-saml-123</saml:NameID></saml:Response>'
    fake_b64 = base64.b64encode(fake_response.encode("utf-8")).decode("utf-8")

    claims = parse_saml_response_claims(fake_b64)
    assert claims["sub"] == "user-saml-123"
    assert claims["username"] == "user-saml-123"


def test_saml_endpoints_disabled_by_default(monkeypatch):
    monkeypatch.delenv("NORMA_FEATURE_AUTH_SAML", raising=False)

    login_resp = client.get("/api/auth/saml/login")
    assert login_resp.status_code == 403
    assert "disabled" in login_resp.json()["detail"]

    acs_resp = client.post("/api/auth/saml/acs", json={"SAMLResponse": "b64"})
    assert acs_resp.status_code == 403

    meta_resp = client.get("/api/auth/saml/metadata")
    assert meta_resp.status_code == 403


def test_saml_endpoints_enabled_with_flag(monkeypatch):
    monkeypatch.setenv("NORMA_FEATURE_AUTH_SAML", "true")

    login_resp = client.get("/api/auth/saml/login")
    assert login_resp.status_code == 200
    assert "authn_url" in login_resp.json()

    meta_resp = client.get("/api/auth/saml/metadata")
    assert meta_resp.status_code == 200
    assert "EntityDescriptor" in meta_resp.text

    acs_resp = client.post("/api/auth/saml/acs", json={"SAMLResponse": "invalid_b64"})
    assert acs_resp.status_code == 200
    user_data = acs_resp.json()
    assert user_data["username"] == "saml_user"
    assert user_data["email"] == "saml.user@example.com"
