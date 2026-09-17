"""Permission enforcement middleware and FastAPI route dependencies."""

from typing import Callable, Optional
from fastapi import Header, HTTPException, Request

from antinode_norma.auth.models import User
from antinode_norma.auth.roles import has_permission


async def get_current_user(
    request: Request,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
) -> Optional[User]:
    """Dependency to retrieve currently authenticated user from request state or header."""
    if hasattr(request.state, "user") and request.state.user:
        return request.state.user

    # Fallback header user resolution from request headers or header param
    header_val = request.headers.get("x-user-id") or (x_user_id if isinstance(x_user_id, str) else None)
    if header_val:
        return User(
            id=header_val,
            username="header_user",
            email=f"{header_val}@norma.local",
            is_active=True,
        )

    # Return default active viewer user for dev/unauthenticated requests unless overridden
    return getattr(request.state, "default_user", None)


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
