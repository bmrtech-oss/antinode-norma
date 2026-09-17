"""OpenID Connect (OIDC) authentication integration and PKCE helpers."""

import base64
import hashlib
import os
import secrets
import urllib.parse
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from antinode_norma.auth.models import Role, User


class OIDCConfig(BaseModel):
    issuer: str = "https://auth.example.com"
    client_id: str = "norma-client"
    client_secret: Optional[str] = None
    redirect_uri: str = "http://localhost:8000/api/auth/oidc/callback"
    scopes: List[str] = Field(default_factory=lambda: ["openid", "profile", "email"])
    authorization_endpoint: Optional[str] = None
    token_endpoint: Optional[str] = None
    userinfo_endpoint: Optional[str] = None
    jwks_uri: Optional[str] = None

    def get_authorization_endpoint(self) -> str:
        return self.authorization_endpoint or f"{self.issuer.rstrip('/')}/protocol/openid-connect/auth"

    def get_token_endpoint(self) -> str:
        return self.token_endpoint or f"{self.issuer.rstrip('/')}/protocol/openid-connect/token"


def generate_pkce_pair() -> Tuple[str, str]:
    """Generate a high-entropy PKCE code_verifier and S256 code_challenge."""
    raw_bytes = os.urandom(32)
    code_verifier = base64.urlsafe_b64encode(raw_bytes).decode("utf-8").rstrip("=")

    digest = hashlib.sha256(code_verifier.encode("utf-8")).digest()
    code_challenge = base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")

    return code_verifier, code_challenge


def build_authorization_url(config: OIDCConfig, state: str, code_challenge: str) -> str:
    """Build the full OIDC authorization redirect URL with PKCE S256 parameters."""
    base_url = config.get_authorization_endpoint()
    params = {
        "client_id": config.client_id,
        "redirect_uri": config.redirect_uri,
        "response_type": "code",
        "scope": " ".join(config.scopes),
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    return f"{base_url}?{urllib.parse.urlencode(params)}"


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
