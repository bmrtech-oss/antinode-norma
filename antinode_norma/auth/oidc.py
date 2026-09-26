"""OpenID Connect (OIDC) authentication integration and PKCE helpers."""

import base64
import hashlib
import hmac
import httpx
import jwt
import os
import threading
import time
import urllib.parse
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from antinode_norma.auth.models import Role, User


class OIDCConfig(BaseModel):
    issuer: str = "https://auth.example.com"
    client_id: str = "norma-client"
    client_secret: Optional[str] = None
    redirect_uri: str = "http://localhost:8000/api/auth/oidc/callback"
    scopes: List[str] = Field(default_factory=lambda: ["openid", "profile", "email"])
    discovery_url: Optional[str] = None
    require_https: bool = False
    authorization_endpoint: Optional[str] = None
    token_endpoint: Optional[str] = None
    userinfo_endpoint: Optional[str] = None
    jwks_uri: Optional[str] = None

    def get_authorization_endpoint(self) -> str:
        if not self.issuer:
            raise ValueError("OIDC issuer or discovery metadata is required")
        return self.authorization_endpoint or f"{self.issuer.rstrip('/')}/protocol/openid-connect/auth"

    def get_token_endpoint(self) -> str:
        if not self.issuer:
            raise ValueError("OIDC issuer or discovery metadata is required")
        return self.token_endpoint or f"{self.issuer.rstrip('/')}/protocol/openid-connect/token"


def generate_pkce_pair() -> Tuple[str, str]:
    """Generate a high-entropy PKCE code_verifier and S256 code_challenge."""
    raw_bytes = os.urandom(32)
    code_verifier = base64.urlsafe_b64encode(raw_bytes).decode("utf-8").rstrip("=")

    digest = hashlib.sha256(code_verifier.encode("utf-8")).digest()
    code_challenge = base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")

    return code_verifier, code_challenge


def build_authorization_url(
    config: OIDCConfig,
    state: str,
    code_challenge: str,
    nonce: Optional[str] = None,
) -> str:
    """Build the full OIDC authorization redirect URL with PKCE S256 parameters."""
    base_url = config.authorization_endpoint or config.get_authorization_endpoint()
    params = {
        "client_id": config.client_id,
        "redirect_uri": config.redirect_uri,
        "response_type": "code",
        "scope": " ".join(config.scopes),
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    if nonce:
        params["nonce"] = nonce
    return f"{base_url}?{urllib.parse.urlencode(params)}"


class OIDCProviderError(ValueError):
    """Raised when discovery, token exchange, or ID-token validation fails."""


class OIDCTransactionStore:
    """Process-local, one-time store for short-lived OIDC state and PKCE data."""

    def __init__(self, ttl_seconds: int = 600) -> None:
        self._ttl_seconds = ttl_seconds
        self._transactions: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def create(
        self,
        state: str,
        *,
        verifier: str,
        nonce: str,
        config: OIDCConfig,
        return_to: str = "/",
    ) -> None:
        with self._lock:
            self._purge_expired()
            self._transactions[state] = {
                "verifier": verifier,
                "nonce": nonce,
                "config": config,
                "return_to": return_to,
                "expires_at": time.monotonic() + self._ttl_seconds,
            }

    def consume(self, state: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            transaction = self._transactions.pop(state, None)
            if not transaction or transaction["expires_at"] <= time.monotonic():
                return None
            return transaction

    def _purge_expired(self) -> None:
        now = time.monotonic()
        expired = [
            state
            for state, transaction in self._transactions.items()
            if transaction["expires_at"] <= now
        ]
        for state in expired:
            del self._transactions[state]


def _validate_endpoint(url: str, *, require_https: bool) -> None:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise OIDCProviderError("OIDC metadata contains an invalid endpoint")
    if parsed.username or parsed.password or parsed.fragment:
        raise OIDCProviderError("OIDC metadata contains an unsafe endpoint")
    if require_https and parsed.scheme != "https":
        raise OIDCProviderError("OIDC metadata endpoints must use HTTPS")


async def discover_provider(config: OIDCConfig, client: httpx.AsyncClient) -> Dict[str, Any]:
    discovery_url = config.discovery_url or (
        f"{config.issuer.rstrip('/')}/.well-known/openid-configuration"
    )
    _validate_endpoint(discovery_url, require_https=config.require_https)
    try:
        response = await client.get(discovery_url)
        response.raise_for_status()
        metadata = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise OIDCProviderError("Unable to load OIDC discovery metadata") from exc
    if not isinstance(metadata, dict):
        raise OIDCProviderError("OIDC discovery metadata must be a JSON object")

    issuer = metadata.get("issuer")
    if not isinstance(issuer, str) or not issuer:
        raise OIDCProviderError("OIDC discovery metadata is missing its issuer")
    if config.issuer and config.issuer != "https://auth.example.com" and issuer != config.issuer:
        raise OIDCProviderError("OIDC discovery issuer does not match configured issuer")
    _validate_endpoint(issuer, require_https=config.require_https)

    for field_name in ("authorization_endpoint", "token_endpoint", "jwks_uri"):
        endpoint = metadata.get(field_name)
        if not isinstance(endpoint, str) or not endpoint:
            raise OIDCProviderError(f"OIDC discovery metadata is missing {field_name}")
        _validate_endpoint(endpoint, require_https=config.require_https)

    return metadata


async def exchange_code_and_validate_id_token(
    config: OIDCConfig,
    *,
    code: str,
    verifier: str,
    nonce: str,
    client: httpx.AsyncClient,
) -> Dict[str, Any]:
    """Exchange an authorization code and validate the returned OIDC ID token."""
    metadata = await discover_provider(config, client)
    try:
        token_response = await client.post(
            metadata["token_endpoint"],
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": config.redirect_uri,
                "code_verifier": verifier,
            },
            auth=(config.client_id, config.client_secret or ""),
        )
        token_response.raise_for_status()
        token_data = token_response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise OIDCProviderError("OIDC authorization code exchange failed") from exc
    if not isinstance(token_data, dict):
        raise OIDCProviderError("OIDC token response must be a JSON object")

    id_token = token_data.get("id_token")
    if not isinstance(id_token, str) or not id_token:
        raise OIDCProviderError("OIDC token response did not contain an ID token")

    try:
        jwks_response = await client.get(metadata["jwks_uri"])
        jwks_response.raise_for_status()
        jwks_payload = jwks_response.json()
        if not isinstance(jwks_payload, dict) or not isinstance(jwks_payload.get("keys"), list):
            raise OIDCProviderError("OIDC JWKS response must contain a keys array")
        jwks = jwks_payload["keys"]
        header = jwt.get_unverified_header(id_token)
    except (httpx.HTTPError, ValueError, jwt.PyJWTError, OIDCProviderError) as exc:
        raise OIDCProviderError("Unable to load OIDC signing keys") from exc

    key_id = header.get("kid")
    algorithm = header.get("alg")
    jwk_data = next(
        (key for key in jwks if isinstance(key, dict) and key.get("kid") == key_id),
        None,
    )
    supported_algorithms = {
        "RS256", "RS384", "RS512", "PS256", "PS384", "PS512",
        "ES256", "ES384", "ES512",
    }
    if (
        not jwk_data
        or algorithm not in supported_algorithms
        or jwk_data.get("use", "sig") != "sig"
        or jwk_data.get("alg", algorithm) != algorithm
    ):
        raise OIDCProviderError("OIDC ID token uses an unknown signing key or algorithm")

    try:
        signing_key = jwt.PyJWK.from_dict(jwk_data, algorithm=algorithm)
        claims = jwt.decode(
            id_token,
            signing_key.key,
            algorithms=[algorithm],
            audience=config.client_id,
            issuer=metadata["issuer"],
            options={"require": ["exp", "iat", "iss", "aud", "sub"]},
            leeway=60,
        )
    except (jwt.PyJWTError, TypeError, ValueError) as exc:
        raise OIDCProviderError("OIDC ID token validation failed") from exc

    audiences = claims.get("aud", [])
    if isinstance(audiences, str):
        audiences = [audiences]
    authorized_party = claims.get("azp")
    if (len(audiences) > 1 and authorized_party != config.client_id) or (
        authorized_party and authorized_party != config.client_id
    ):
        raise OIDCProviderError("OIDC ID token authorized party is invalid")
    token_nonce = claims.get("nonce")
    if not isinstance(token_nonce, str) or not hmac.compare_digest(token_nonce, nonce):
        raise OIDCProviderError("OIDC ID token nonce validation failed")
    return claims


def map_claims_to_user(claims: Dict[str, str], roles: Optional[List[Role]] = None) -> User:
    """Map OIDC ID token or userinfo claims to a Norma User model."""
    sub = claims.get("sub", "")
    email = claims.get("email", f"{sub}@oidc.user" if sub else "user@oidc.local")
    username = (
        claims.get("preferred_username")
        or claims.get("nickname")
        or (email.split("@")[0] if "@" in email else "oidc_user")
    )
    display_name = claims.get("name") or claims.get("given_name")

    user_kwargs = {
        "username": username,
        "email": email,
        "roles": roles if roles else [Role.VIEWER],
        "display_name": display_name,
        "is_active": True,
    }
    if sub:
        user_kwargs["id"] = sub

    return User(**user_kwargs)
