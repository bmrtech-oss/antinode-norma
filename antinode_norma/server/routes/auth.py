"""OIDC & SAML Authentication routes for Antinode Norma API."""

import hashlib
import os
import secrets
import httpx
from datetime import datetime, timezone
from typing import Dict, List, Optional
from urllib.parse import urlsplit, urlunsplit
from fastapi import APIRouter, HTTPException, Query, Request, Response
from pydantic import BaseModel
from starlette.responses import RedirectResponse

from antinode_norma.auth.oidc import (
    OIDCProviderError,
    OIDCTransactionStore,
    build_authorization_url,
    discover_provider,
    exchange_code_and_validate_id_token,
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
from antinode_norma.auth.roles import get_user_permissions
from antinode_norma.auth.config import (
    CSRF_COOKIE_NAME,
    SESSION_COOKIE_NAME,
    AuthSettings,
    canonical_origin,
    load_auth_settings,
)
from antinode_norma.core.features import FeatureFlagResolver
from antinode_norma import database as auth_database

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# State transactions are short-lived and consumed once; durable shared storage
# is a follow-up requirement before multi-worker production rollout.
_OIDC_TRANSACTIONS = OIDCTransactionStore()
_ACTIVE_USERS: Dict[str, User] = {}


class LoginInitiateResponse(BaseModel):
    authorization_url: str
    state: str


class AuthMeResponse(BaseModel):
    user: User
    permissions: List[str]
    session_expires_at: str


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


def _validated_return_to(value: Optional[str], settings: AuthSettings) -> str:
    default_origin = settings.allowed_origins[0] if settings.allowed_origins else ""
    default_target = f"{default_origin}/" if default_origin else "/"
    if not value:
        return default_target
    if len(value) > 2048 or any(ord(char) < 32 for char in value) or "\\" in value:
        raise HTTPException(status_code=400, detail="Invalid post-login return path")

    parsed = urlsplit(value)
    if parsed.fragment or parsed.username or parsed.password:
        raise HTTPException(status_code=400, detail="Invalid post-login return path")
    if not parsed.scheme and not parsed.netloc:
        if not parsed.path.startswith("/") or parsed.path.startswith("//"):
            raise HTTPException(status_code=400, detail="Invalid post-login return path")
        if not default_origin:
            return urlunsplit(("", "", parsed.path, parsed.query, ""))
        return urlunsplit((*urlsplit(default_origin)[:2], parsed.path, parsed.query, ""))

    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise HTTPException(status_code=400, detail="Invalid post-login return path")
    try:
        origin = canonical_origin(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid post-login return path") from exc
    if origin not in settings.allowed_origins:
        raise HTTPException(status_code=400, detail="Post-login origin is not allowed")
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path or "/", parsed.query, ""))


@router.get("/oidc/login", response_model=LoginInitiateResponse)
async def oidc_login(return_to: Optional[str] = Query(None)):
    """Initiate OIDC authentication with PKCE parameters."""
    settings = load_auth_settings()
    if settings.mode != "oidc":
        raise HTTPException(status_code=503, detail="OIDC authentication is not configured")
    return_target = _validated_return_to(return_to, settings)
    config = settings.to_oidc_config()
    state = secrets.token_urlsafe(16)
    nonce = secrets.token_urlsafe(32)
    code_verifier, code_challenge = generate_pkce_pair()

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            metadata = await discover_provider(config, client)
    except OIDCProviderError as exc:
        raise HTTPException(status_code=502, detail="Unable to initialize OIDC login") from exc
    config.authorization_endpoint = metadata["authorization_endpoint"]
    config.token_endpoint = metadata["token_endpoint"]
    config.jwks_uri = metadata["jwks_uri"]
    if not config.issuer:
        config.issuer = metadata["issuer"]
    _OIDC_TRANSACTIONS.create(
        state,
        verifier=code_verifier,
        nonce=nonce,
        config=config,
        return_to=return_target,
    )
    auth_url = build_authorization_url(
        config, state=state, code_challenge=code_challenge, nonce=nonce
    )

    return LoginInitiateResponse(
        authorization_url=auth_url,
        state=state,
    )


@router.get("/oidc/callback", include_in_schema=False)
async def oidc_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
):
    """Callback route to exchange code for tokens and map user claims."""
    if error:
        raise HTTPException(status_code=401, detail="OIDC authentication was not completed")
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code missing")
    if not state:
        raise HTTPException(status_code=400, detail="OIDC state is missing")
    transaction = _OIDC_TRANSACTIONS.consume(state)
    if not transaction:
        raise HTTPException(status_code=400, detail="OIDC state is invalid, expired, or already used")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            claims = await exchange_code_and_validate_id_token(
                transaction["config"],
                code=code,
                verifier=transaction["verifier"],
                nonce=transaction["nonce"],
                client=client,
            )
    except OIDCProviderError as exc:
        raise HTTPException(status_code=502, detail="OIDC provider validation failed") from exc
    user = map_claims_to_user(claims)
    _ACTIVE_USERS[user.id] = user
    expires_at = datetime.fromtimestamp(claims["exp"], tz=timezone.utc)
    now = datetime.now(timezone.utc)
    if expires_at <= now:
        raise HTTPException(status_code=401, detail="OIDC session has expired")
    session_token = secrets.token_urlsafe(32)
    csrf_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(session_token.encode("utf-8")).hexdigest()
    auth_database.save_auth_session(
        os.getenv("DATABASE_URL", "sqlite:///.runtime/norma.db"),
        {
            "session_token_hash": token_hash,
            "user_id": user.id,
            "user": user.model_dump(mode="json"),
            "issuer": claims["iss"],
            "subject": claims["sub"],
            "idp_sid": claims.get("sid"),
            "expires_at": expires_at.isoformat(),
            "created_at": now.isoformat(),
            "csrf_token_hash": hashlib.sha256(csrf_token.encode("utf-8")).hexdigest(),
        },
    )
    cookie_settings = load_auth_settings()
    cookie_options = {
        "max_age": max(1, int((expires_at - now).total_seconds())),
        "secure": cookie_settings.is_production,
        "samesite": cookie_settings.session_cookie_samesite,
        "path": "/",
    }
    redirect_response = RedirectResponse(transaction["return_to"], status_code=303)
    redirect_response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_token,
        httponly=True,
        **cookie_options,
    )
    redirect_response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf_token,
        httponly=False,
        **cookie_options,
    )
    return redirect_response


def _load_session(request: Request) -> dict:
    session_token = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_token:
        raise HTTPException(status_code=401, detail="Authentication required")
    token_hash = hashlib.sha256(session_token.encode("utf-8")).hexdigest()
    session = auth_database.load_auth_session(
        os.getenv("DATABASE_URL", "sqlite:///.runtime/norma.db"), token_hash
    )
    if session is None:
        raise HTTPException(status_code=401, detail="Session is invalid or expired")
    return session


@router.get("/me", response_model=AuthMeResponse)
async def auth_me(request: Request):
    """Return the user and permissions bound to the active server session."""
    session = _load_session(request)
    user = User.model_validate(session["user"])
    return AuthMeResponse(
        user=user,
        permissions=sorted(get_user_permissions(user)),
        session_expires_at=session["expires_at"],
    )


@router.get("/oidc/me", response_model=User, include_in_schema=False)
async def oidc_me(request: Request):
    """Compatibility alias for the session-bound current-user endpoint."""
    return User.model_validate(_load_session(request)["user"])


@router.post("/logout")
async def logout(request: Request, response: Response):
    """Revoke the current server-side session and clear its browser cookie."""
    session_token = request.cookies.get(SESSION_COOKIE_NAME)
    if session_token:
        token_hash = hashlib.sha256(session_token.encode("utf-8")).hexdigest()
        auth_database.revoke_auth_session(
            os.getenv("DATABASE_URL", "sqlite:///.runtime/norma.db"), token_hash
        )
    settings = load_auth_settings()
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path="/",
        httponly=True,
        secure=settings.is_production,
        samesite=settings.session_cookie_samesite,
    )
    response.delete_cookie(
        key=CSRF_COOKIE_NAME,
        path="/",
        httponly=False,
        secure=settings.is_production,
        samesite=settings.session_cookie_samesite,
    )
    return {"status": "logged_out"}


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
