"""Validated deployment configuration for browser authentication."""

from dataclasses import dataclass, field
import os
from typing import Mapping, Optional
from urllib.parse import urlsplit


class AuthConfigurationError(ValueError):
    """Raised when authentication deployment settings are incomplete or unsafe."""


SESSION_COOKIE_NAME = "norma_session"
CSRF_COOKIE_NAME = "norma_csrf"


def _validate_url(name: str, value: str, *, production: bool) -> str:
    parsed = urlsplit(value)
    try:
        has_valid_port = parsed.port is None or 1 <= parsed.port <= 65535
    except ValueError:
        has_valid_port = False

    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
        or not has_valid_port
    ):
        raise AuthConfigurationError(f"{name} must be an absolute HTTP(S) URL")
    if production and parsed.scheme != "https":
        raise AuthConfigurationError(f"{name} must use HTTPS in production")
    return value


def canonical_origin(value: str) -> str:
    parsed = urlsplit(value)
    hostname = (parsed.hostname or "").lower()
    if ":" in hostname and not hostname.startswith("["):
        hostname = f"[{hostname}]"
    port = parsed.port
    if port is not None and not (
        (parsed.scheme == "http" and port == 80)
        or (parsed.scheme == "https" and port == 443)
    ):
        hostname = f"{hostname}:{port}"
    return f"{parsed.scheme.lower()}://{hostname}"


def _parse_allowed_origins(value: str, *, production: bool) -> tuple[str, ...]:
    origins = []
    for item in value.split(","):
        origin = item.strip()
        if not origin:
            continue
        validated = _validate_url("NORMA_AUTH_ALLOWED_ORIGINS entry", origin, production=production)
        parsed = urlsplit(validated)
        if parsed.path not in {"", "/"} or parsed.query:
            raise AuthConfigurationError(
                "NORMA_AUTH_ALLOWED_ORIGINS entries must be origins without paths or queries"
            )
        normalized = canonical_origin(validated)
        if normalized == "*":
            raise AuthConfigurationError("NORMA_AUTH_ALLOWED_ORIGINS cannot contain '*'")
        if normalized not in origins:
            origins.append(normalized)
    return tuple(origins)


@dataclass(frozen=True)
class AuthSettings:
    environment: str
    mode: str
    allow_identity_headers: bool
    oidc_issuer: Optional[str]
    oidc_discovery_url: Optional[str]
    oidc_client_id: Optional[str]
    oidc_client_secret: Optional[str] = field(repr=False)
    oidc_redirect_uri: Optional[str]
    allowed_origins: tuple[str, ...]

    @property
    def is_production(self) -> bool:
        return self.environment in {"prod", "production"}

    @property
    def session_cookie_samesite(self) -> str:
        if not self.is_production or not self.oidc_redirect_uri:
            return "lax"
        api_origin = canonical_origin(self.oidc_redirect_uri)
        return "none" if any(origin != api_origin for origin in self.allowed_origins) else "lax"

    def to_oidc_config(self):
        """Build the existing OIDC URL config from validated deployment values."""
        from antinode_norma.auth.oidc import OIDCConfig

        return OIDCConfig(
            issuer=self.oidc_issuer or "",
            discovery_url=self.oidc_discovery_url,
            client_id=self.oidc_client_id or "norma-client",
            client_secret=self.oidc_client_secret,
            redirect_uri=self.oidc_redirect_uri
            or "http://localhost:8000/api/auth/oidc/callback",
            require_https=self.is_production,
        )

    @classmethod
    def from_environment(
        cls, environ: Optional[Mapping[str, str]] = None
    ) -> "AuthSettings":
        values = os.environ if environ is None else environ
        environment = values.get("NORMA_ENVIRONMENT", "development").strip().lower()
        mode = values.get("NORMA_AUTH_MODE", "disabled").strip().lower()
        identity_header_setting = values.get(
            "NORMA_AUTH_ALLOW_IDENTITY_HEADERS", "false"
        ).strip().lower()
        if mode not in {"disabled", "oidc"}:
            raise AuthConfigurationError("NORMA_AUTH_MODE must be 'disabled' or 'oidc'")
        if identity_header_setting not in {"true", "false"}:
            raise AuthConfigurationError(
                "NORMA_AUTH_ALLOW_IDENTITY_HEADERS must be 'true' or 'false'"
            )

        production = environment in {"prod", "production"}
        allow_identity_headers = identity_header_setting == "true"
        issuer = values.get("NORMA_OIDC_ISSUER", "").strip() or None
        discovery_url = values.get("NORMA_OIDC_DISCOVERY_URL", "").strip() or None
        client_id = values.get("NORMA_OIDC_CLIENT_ID", "").strip() or None
        client_secret = values.get("NORMA_OIDC_CLIENT_SECRET", "").strip() or None
        redirect_uri = values.get("NORMA_OIDC_REDIRECT_URI", "").strip() or None

        if issuer:
            issuer = _validate_url("NORMA_OIDC_ISSUER", issuer, production=production)
        if discovery_url:
            discovery_url = _validate_url(
                "NORMA_OIDC_DISCOVERY_URL", discovery_url, production=production
            )
        if redirect_uri:
            redirect_uri = _validate_url(
                "NORMA_OIDC_REDIRECT_URI", redirect_uri, production=production
            )
        allowed_origins = _parse_allowed_origins(
            values.get("NORMA_AUTH_ALLOWED_ORIGINS", ""), production=production
        )

        settings = cls(
            environment=environment,
            mode=mode,
            allow_identity_headers=allow_identity_headers,
            oidc_issuer=issuer,
            oidc_discovery_url=discovery_url,
            oidc_client_id=client_id,
            oidc_client_secret=client_secret,
            oidc_redirect_uri=redirect_uri,
            allowed_origins=allowed_origins,
        )

        if production and mode != "oidc":
            raise AuthConfigurationError(
                "Production requires NORMA_AUTH_MODE=oidc; authentication cannot be disabled"
            )
        if allow_identity_headers and production:
            raise AuthConfigurationError(
                "NORMA_AUTH_ALLOW_IDENTITY_HEADERS cannot be enabled in production"
            )
        if allow_identity_headers and mode != "disabled":
            raise AuthConfigurationError(
                "NORMA_AUTH_ALLOW_IDENTITY_HEADERS requires NORMA_AUTH_MODE=disabled"
            )
        if mode == "oidc":
            missing = []
            if not issuer and not discovery_url:
                missing.append("NORMA_OIDC_ISSUER or NORMA_OIDC_DISCOVERY_URL")
            if not client_id:
                missing.append("NORMA_OIDC_CLIENT_ID")
            if not client_secret:
                missing.append("NORMA_OIDC_CLIENT_SECRET")
            if not redirect_uri:
                missing.append("NORMA_OIDC_REDIRECT_URI")
            if not allowed_origins:
                missing.append("NORMA_AUTH_ALLOWED_ORIGINS")
            if missing:
                raise AuthConfigurationError(
                    "OIDC authentication requires: " + ", ".join(missing)
                )

        return settings


def load_auth_settings() -> AuthSettings:
    """Load and validate auth settings from the process environment."""
    return AuthSettings.from_environment()