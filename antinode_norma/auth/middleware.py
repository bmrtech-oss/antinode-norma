"""Permission enforcement middleware and FastAPI route dependencies."""

import hashlib
import hmac
import os
from typing import Callable, Optional
from urllib.parse import urlsplit
from fastapi import Header, HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from antinode_norma import database
from antinode_norma.auth.config import CSRF_COOKIE_NAME, SESSION_COOKIE_NAME, load_auth_settings
from antinode_norma.auth.models import Role, User
from antinode_norma.auth.roles import has_permission


class AuthCSRFMiddleware(BaseHTTPMiddleware):
    """Require origin and session-bound CSRF proof on cookie-authenticated writes."""

    async def dispatch(self, request: Request, call_next):
        if request.method in {"GET", "HEAD", "OPTIONS", "TRACE"}:
            return await call_next(request)
        if request.url.path.endswith("/backchannel-logout"):
            return await call_next(request)

        session_token = request.cookies.get(SESSION_COOKIE_NAME)
        if not session_token:
            return await call_next(request)

        settings = load_auth_settings()
        origin = request.headers.get("origin")
        if not origin:
            referer = request.headers.get("referer")
            if referer:
                parsed_referer = urlsplit(referer)
                if parsed_referer.scheme and parsed_referer.netloc:
                    origin = f"{parsed_referer.scheme}://{parsed_referer.netloc}"
        if not origin or origin not in settings.allowed_origins:
            return JSONResponse(
                status_code=403,
                content={"detail": "Request origin is not allowed"},
            )

        csrf_cookie = request.cookies.get(CSRF_COOKIE_NAME)
        csrf_header = request.headers.get("x-csrf-token")
        if not csrf_cookie or not csrf_header or not hmac.compare_digest(csrf_cookie, csrf_header):
            return JSONResponse(status_code=403, content={"detail": "CSRF validation failed"})

        token_hash = hashlib.sha256(session_token.encode("utf-8")).hexdigest()
        session = database.load_auth_session(
            os.getenv("DATABASE_URL", "sqlite:///.runtime/norma.db"), token_hash
        )
        csrf_hash = hashlib.sha256(csrf_cookie.encode("utf-8")).hexdigest()
        if not session or not session.get("csrf_token_hash") or not hmac.compare_digest(
            session["csrf_token_hash"], csrf_hash
        ):
            return JSONResponse(status_code=403, content={"detail": "CSRF validation failed"})

        return await call_next(request)


async def get_current_user(
    request: Request,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
) -> Optional[User]:
    """Dependency to retrieve currently authenticated user from request state or header."""
    if hasattr(request.state, "user") and request.state.user:
        return request.state.user

    session_token = request.cookies.get(SESSION_COOKIE_NAME)
    if session_token:
        token_hash = hashlib.sha256(session_token.encode("utf-8")).hexdigest()
        session = database.load_auth_session(
            os.getenv("DATABASE_URL", "sqlite:///.runtime/norma.db"), token_hash
        )
        return User.model_validate(session["user"]) if session else None

    settings = load_auth_settings()
    if (
        not settings.allow_identity_headers
        or settings.is_production
        or settings.mode != "disabled"
    ):
        return None

    # Header identity is a local/test fixture only, never a production credential.
    header_val = request.headers.get("x-user-id") or (x_user_id if isinstance(x_user_id, str) else None)
    if header_val:
        roles = [Role.ADMIN] if "admin" in header_val.lower() else [Role.VIEWER]
        return User(
            id=header_val,
            username="header_user",
            email=f"{header_val}@norma.local",
            roles=roles,
            is_active=True,
            tenant_id=(x_tenant_id if isinstance(x_tenant_id, str) else None)
            or request.headers.get("x-tenant-id") or "default",
        )

    # Return default active viewer user for dev/unauthenticated requests unless overridden
    return getattr(request.state, "default_user", None)


def ensure_resource_owner(user: User, resource: dict) -> None:
    """Require a resource to belong to the authenticated user and tenant.

    Legacy rows without ownership metadata remain readable to authenticated users
    so existing local databases continue to work; all newly-created rows carry
    both fields.
    """
    owner_id = resource.get("owner_id")
    tenant_id = resource.get("tenant_id")
    if tenant_id and tenant_id != (user.tenant_id or "default"):
        raise HTTPException(status_code=404, detail="Resource not found")
    if owner_id and owner_id != user.id and Role.ADMIN not in user.roles:
        raise HTTPException(status_code=404, detail="Resource not found")


def requires_permission(permission: str) -> Callable:
    """FastAPI route dependency factory enforcing permission checks.

    Raises HTTP 401 Unauthenticated if user is missing or inactive.
    Raises HTTP 403 Forbidden if user lacks required permission.
    """
    async def dependency(request: Request) -> User:
        user = await get_current_user(request)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=401,
                detail="Authentication required to access this resource",
            )

        if not has_permission(user, permission):
            raise HTTPException(
                status_code=403,
                detail=f"Permission '{permission}' required to access this resource",
            )

        return user

    return dependency


def log_user_action(
    request: Request,
    user: Optional[User],
    action: str,
    resource: str,
    result: str = "success",
    payload: Optional[dict] = None,
) -> None:
    """Helper function to record a user action event into audit trail."""
    from antinode_norma.server.routes.audit import audit_log

    user_id = user.id if user else "anonymous"
    client_ip = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("user-agent", "unknown")

    audit_log.record_user_action(
        user_id=user_id,
        action=action,
        resource=resource,
        result=result,
        ip=client_ip,
        user_agent=user_agent,
        payload={
            **(payload or {}),
            "tenant_id": user.tenant_id if user else "default",
        },
    )
