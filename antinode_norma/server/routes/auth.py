"""OIDC & SAML Authentication routes for Antinode Norma API."""

import secrets
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel

from antinode_norma.auth.oidc import (
    OIDCConfig,
    build_authorization_url,
    generate_pkce_pair,
    map_claims_to_user,
)
from antinode_norma.auth.saml import (
    SAMLConfig,
    build_authn_request,
    generate_sp_metadata,
    parse_saml_response_claims,
)
from antinode_norma.auth.models import User
from antinode_norma.auth.roles import ADMIN_WRITE
from antinode_norma.auth.middleware import requires_permission
from antinode_norma.core.features import FeatureFlagResolver

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# In-memory mock session/state store for demonstration/testing
_OIDC_SESSIONS: Dict[str, Dict[str, Any]] = {}
_ACTIVE_USERS: Dict[str, User] = {}


class LoginInitiateResponse(BaseModel):
    authorization_url: str
    state: str
    code_verifier: str


class CallbackRequest(BaseModel):
    code: str
    state: str
    code_verifier: str


class SAMLACSRequest(BaseModel):
    SAMLResponse: str


class SAMLLoginResponse(BaseModel):
    authn_url: str


def _check_saml_enabled():
    resolver = FeatureFlagResolver()
    if not resolver.is_enabled("auth_saml"):
        raise HTTPException(
            status_code=403,
            detail="SAML 2.0 authentication feature flag (auth_saml) is disabled",
        )


@router.get("/oidc/login", response_model=LoginInitiateResponse)
async def oidc_login():
    """Initiate OIDC authentication with PKCE parameters."""
    config = OIDCConfig()
    state = secrets.token_urlsafe(16)
    code_verifier, code_challenge = generate_pkce_pair()

    auth_url = build_authorization_url(config, state=state, code_challenge=code_challenge)

    _OIDC_SESSIONS[state] = {
        "code_verifier": code_verifier,
        "config": config,
    }

    return LoginInitiateResponse(
        authorization_url=auth_url,
        state=state,
        code_verifier=code_verifier,
    )


@router.post("/oidc/callback", response_model=User)
async def oidc_callback(req: CallbackRequest):
    """Callback route to exchange code for tokens and map user claims."""
    if not req.code:
        raise HTTPException(status_code=400, detail="Authorization code missing")

    # Simulated claims mapping for OIDC callback
    claims = {
        "sub": f"user-{req.state[:8]}",
        "email": "oidc.user@example.com",
        "preferred_username": "oidc_user",
        "name": "OIDC User",
    }
    user = map_claims_to_user(claims)
    _ACTIVE_USERS[user.id] = user
    return user


@router.get("/oidc/me", response_model=User)
async def oidc_me(user_id: Optional[str] = Query(None)):
    """Retrieve current OIDC user profile."""
    if user_id and user_id in _ACTIVE_USERS:
        return _ACTIVE_USERS[user_id]

    # Return default active user profile if no specific user_id provided
    return User(
        username="current_user",
        email="user@norma.local",
        display_name="Authenticated User",
    )


@router.get("/saml/login", response_model=SAMLLoginResponse)
async def saml_login():
    """Initiate SAML 2.0 authentication redirect (flagged)."""
    _check_saml_enabled()
    config = SAMLConfig()
    authn_url = build_authn_request(config)
    return SAMLLoginResponse(authn_url=authn_url)


@router.post("/saml/acs", response_model=User)
async def saml_acs(req: SAMLACSRequest):
    """SAML Assertion Consumer Service route (flagged)."""
    _check_saml_enabled()
    claims = parse_saml_response_claims(req.SAMLResponse)
    user = User(
        id=claims["sub"],
        username=claims["username"],
        email=claims["email"],
        display_name=claims.get("name"),
    )
    _ACTIVE_USERS[user.id] = user
    return user


@router.get("/saml/metadata")
async def saml_metadata():
    """Get SAML Service Provider XML metadata (flagged)."""
    _check_saml_enabled()
    config = SAMLConfig()
    xml_metadata = generate_sp_metadata(config)
    return Response(content=xml_metadata, media_type="application/xml")


@router.get("/protected-admin-route", dependencies=[Depends(requires_permission(ADMIN_WRITE))])
async def protected_admin_route():
    """Protected admin settings route requiring ADMIN_WRITE permission."""
    return {"status": "ok", "message": "Admin access granted"}
