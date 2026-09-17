"""OIDC Authentication routes for Antinode Norma API."""

import secrets
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from antinode_norma.auth.oidc import (
    OIDCConfig,
    build_authorization_url,
    generate_pkce_pair,
    map_claims_to_user,
)
from antinode_norma.auth.models import User

router = APIRouter(prefix="/api/auth/oidc", tags=["Authentication"])

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


@router.get("/login", response_model=LoginInitiateResponse)
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


@router.post("/callback", response_model=User)
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


@router.get("/me", response_model=User)
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
