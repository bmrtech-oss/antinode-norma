"""Backend unit tests for AUTH-1-T05: Validated Return Path & Open Redirect Prevention."""

import pytest
from fastapi import HTTPException

from antinode_norma.auth.config import AuthSettings
from antinode_norma.server.routes.auth import _validated_return_to


def _settings():
    return AuthSettings.from_environment(
        {
            "NORMA_AUTH_MODE": "oidc",
            "NORMA_OIDC_ISSUER": "https://identity.example.test",
            "NORMA_OIDC_CLIENT_ID": "norma-web",
            "NORMA_OIDC_CLIENT_SECRET": "secret",
            "NORMA_OIDC_REDIRECT_URI": "http://localhost:8000/api/auth/oidc/callback",
            "NORMA_AUTH_ALLOWED_ORIGINS": "http://localhost:3000, https://app.norma.local",
        }
    )


def test_validated_return_to_allows_valid_local_paths():
    settings = _settings()

    target = _validated_return_to("/dashboard", settings)
    assert target == "http://localhost:3000/dashboard"

    target_params = _validated_return_to("/approvals?filter=pending", settings)
    assert target_params == "http://localhost:3000/approvals?filter=pending"


def test_validated_return_to_allows_configured_origins():
    settings = _settings()

    target = _validated_return_to("https://app.norma.local/reports", settings)
    assert target == "https://app.norma.local/reports"


def test_validated_return_to_rejects_unallowed_external_origins():
    settings = _settings()

    with pytest.raises(HTTPException) as exc_info:
        _validated_return_to("https://attacker.example.test/steal", settings)
    assert exc_info.value.status_code == 400
    assert "not allowed" in exc_info.value.detail


def test_validated_return_to_rejects_malformed_and_unsafe_paths():
    settings = _settings()

    invalid_inputs = [
        "//attacker.example.test/steal",
        "/path\\with\\backslash",
        "/path\nwith\nnewline",
        "javascript:alert(1)",
        "https://user:pass@app.norma.local/login",
    ]

    for item in invalid_inputs:
        with pytest.raises(HTTPException) as exc_info:
            _validated_return_to(item, settings)
        assert exc_info.value.status_code == 400
