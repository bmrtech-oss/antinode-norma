import pytest
from fastapi.testclient import TestClient

from antinode_norma.auth.config import AuthConfigurationError, AuthSettings
from antinode_norma.server.api import app


def test_auth_settings_default_to_auth_disabled_for_development():
    settings = AuthSettings.from_environment({})

    assert settings.environment == "development"
    assert settings.mode == "disabled"
    assert settings.allow_identity_headers is False
    assert settings.allowed_origins == ()
    assert settings.to_oidc_config().client_id == "norma-client"


def test_identity_header_mode_requires_explicit_local_opt_in():
    settings = AuthSettings.from_environment(
        {
            "NORMA_AUTH_MODE": "disabled",
            "NORMA_AUTH_ALLOW_IDENTITY_HEADERS": "true",
        }
    )

    assert settings.allow_identity_headers is True


def test_identity_header_mode_is_rejected_for_production_and_oidc():
    with pytest.raises(AuthConfigurationError, match="cannot be enabled in production"):
        AuthSettings.from_environment(
            {
                "NORMA_ENVIRONMENT": "production",
                "NORMA_AUTH_MODE": "oidc",
                "NORMA_AUTH_ALLOW_IDENTITY_HEADERS": "true",
                "NORMA_OIDC_ISSUER": "https://identity.example.test",
                "NORMA_OIDC_CLIENT_ID": "norma-web",
                "NORMA_OIDC_CLIENT_SECRET": "secret",
                "NORMA_OIDC_REDIRECT_URI": "https://api.example.test/callback",
                "NORMA_AUTH_ALLOWED_ORIGINS": "https://ui.example.test",
            }
        )

    with pytest.raises(AuthConfigurationError, match="requires NORMA_AUTH_MODE=disabled"):
        AuthSettings.from_environment(
            {
                "NORMA_AUTH_MODE": "oidc",
                "NORMA_AUTH_ALLOW_IDENTITY_HEADERS": "true",
                "NORMA_OIDC_ISSUER": "https://identity.example.test",
                "NORMA_OIDC_CLIENT_ID": "norma-web",
                "NORMA_OIDC_CLIENT_SECRET": "secret",
                "NORMA_OIDC_REDIRECT_URI": "http://api.example.test/callback",
                "NORMA_AUTH_ALLOWED_ORIGINS": "http://ui.example.test",
            }
        )


def test_auth_settings_load_and_normalize_oidc_deployment_values():
    settings = AuthSettings.from_environment(
        {
            "NORMA_AUTH_MODE": "oidc",
            "NORMA_OIDC_ISSUER": "https://identity.example.test/tenant",
            "NORMA_OIDC_CLIENT_ID": "norma-web",
            "NORMA_OIDC_CLIENT_SECRET": "deployment-secret",
            "NORMA_OIDC_REDIRECT_URI": "https://norma.example.test/api/auth/oidc/callback",
            "NORMA_AUTH_ALLOWED_ORIGINS": "https://norma.example.test/, https://admin.example.test",
        }
    )

    assert settings.mode == "oidc"
    assert settings.allowed_origins == (
        "https://norma.example.test",
        "https://admin.example.test",
    )
    oidc_config = settings.to_oidc_config()
    assert oidc_config.issuer == "https://identity.example.test/tenant"
    assert oidc_config.client_id == "norma-web"
    assert oidc_config.client_secret == "deployment-secret"
    assert oidc_config.redirect_uri == "https://norma.example.test/api/auth/oidc/callback"


def test_oidc_mode_requires_complete_deployment_configuration():
    with pytest.raises(AuthConfigurationError, match="NORMA_OIDC_CLIENT_ID"):
        AuthSettings.from_environment({"NORMA_AUTH_MODE": "oidc"})


def test_oidc_discovery_url_is_carried_into_oidc_config():
    settings = AuthSettings.from_environment(
        {
            "NORMA_AUTH_MODE": "oidc",
            "NORMA_OIDC_DISCOVERY_URL": "https://identity.example.test/.well-known/openid-configuration",
            "NORMA_OIDC_CLIENT_ID": "norma-web",
            "NORMA_OIDC_CLIENT_SECRET": "deployment-secret",
            "NORMA_OIDC_REDIRECT_URI": "http://localhost:8000/api/auth/oidc/callback",
            "NORMA_AUTH_ALLOWED_ORIGINS": "http://localhost:3000",
        }
    )

    assert settings.to_oidc_config().discovery_url == (
        "https://identity.example.test/.well-known/openid-configuration"
    )


def test_production_rejects_disabled_authentication():
    with pytest.raises(AuthConfigurationError, match="Production requires"):
        AuthSettings.from_environment({"NORMA_ENVIRONMENT": "production"})


def test_api_startup_rejects_disabled_authentication_in_production(monkeypatch):
    monkeypatch.setenv("NORMA_ENVIRONMENT", "production")
    monkeypatch.delenv("NORMA_AUTH_MODE", raising=False)

    with pytest.raises(AuthConfigurationError, match="Production requires"):
        with TestClient(app):
            pass


def test_production_requires_https_endpoints_and_origins():
    with pytest.raises(AuthConfigurationError, match="must use HTTPS in production"):
        AuthSettings.from_environment(
            {
                "NORMA_ENVIRONMENT": "production",
                "NORMA_AUTH_MODE": "oidc",
                "NORMA_OIDC_ISSUER": "http://identity.example.test",
                "NORMA_OIDC_CLIENT_ID": "norma-web",
                "NORMA_OIDC_CLIENT_SECRET": "deployment-secret",
                "NORMA_OIDC_REDIRECT_URI": "https://norma.example.test/api/auth/oidc/callback",
                "NORMA_AUTH_ALLOWED_ORIGINS": "https://norma.example.test",
            }
        )


def test_allowed_origins_reject_paths_and_wildcard():
    with pytest.raises(AuthConfigurationError, match="without paths or queries"):
        AuthSettings.from_environment(
            {
                "NORMA_AUTH_MODE": "oidc",
                "NORMA_OIDC_ISSUER": "https://identity.example.test",
                "NORMA_OIDC_CLIENT_ID": "norma-web",
                "NORMA_OIDC_CLIENT_SECRET": "deployment-secret",
                "NORMA_OIDC_REDIRECT_URI": "http://localhost:8000/api/auth/oidc/callback",
                "NORMA_AUTH_ALLOWED_ORIGINS": "https://norma.example.test/app",
            }
        )


def test_cookie_samesite_policy_distinguishes_separate_origins():
    common = {
        "NORMA_ENVIRONMENT": "production",
        "NORMA_AUTH_MODE": "oidc",
        "NORMA_OIDC_ISSUER": "https://identity.example.test",
        "NORMA_OIDC_CLIENT_ID": "norma-web",
        "NORMA_OIDC_CLIENT_SECRET": "deployment-secret",
        "NORMA_OIDC_REDIRECT_URI": "https://api.example.test/api/auth/oidc/callback",
    }

    same_origin = AuthSettings.from_environment(
        {**common, "NORMA_AUTH_ALLOWED_ORIGINS": "https://api.example.test"}
    )
    split_origin = AuthSettings.from_environment(
        {**common, "NORMA_AUTH_ALLOWED_ORIGINS": "https://ui.example.test"}
    )

    assert same_origin.session_cookie_samesite == "lax"
    assert split_origin.session_cookie_samesite == "none"


def test_allowed_origins_normalize_case_and_default_ports():
    settings = AuthSettings.from_environment(
        {
            "NORMA_AUTH_MODE": "oidc",
            "NORMA_OIDC_ISSUER": "https://identity.example.test",
            "NORMA_OIDC_CLIENT_ID": "norma-web",
            "NORMA_OIDC_CLIENT_SECRET": "secret",
            "NORMA_OIDC_REDIRECT_URI": "https://api.example.test/api/auth/oidc/callback",
            "NORMA_AUTH_ALLOWED_ORIGINS": "https://UI.example.test:443/",
        }
    )

    assert settings.allowed_origins == ("https://ui.example.test",)