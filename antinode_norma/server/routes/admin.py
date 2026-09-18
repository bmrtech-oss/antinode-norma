"""Admin settings routes for Norma BDD Platform FastAPI server."""

from typing import Dict, Any
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from antinode_norma.auth.middleware import log_user_action, requires_permission
from antinode_norma.auth.models import User
from antinode_norma.auth.roles import ADMIN_WRITE

router = APIRouter(prefix="/api/admin", tags=["Admin"])


class PlatformSettings(BaseModel):
    app_name: str = "Antinode Norma BDD Platform"
    feature_flags: Dict[str, bool] = Field(
        default_factory=lambda: {
            "auth_saml": True,
            "governance_audit": True,
            "governance_approval": True,
            "cache_exact": True,
            "cache_semantic": True,
            "execution_cloud": True,
        }
    )
    max_repair_attempts: int = 3
    audit_retention_days: int = 90


# In-memory platform settings store
_current_settings = PlatformSettings()


@router.get(
    "/settings",
    response_model=PlatformSettings,
    dependencies=[Depends(requires_permission(ADMIN_WRITE))],
)
async def get_admin_settings() -> PlatformSettings:
    """Retrieves current platform configuration settings."""
    return _current_settings


@router.put(
    "/settings",
    response_model=PlatformSettings,
)
async def update_admin_settings(
    request: Request,
    new_settings: PlatformSettings,
    user: User = Depends(requires_permission(ADMIN_WRITE)),
) -> PlatformSettings:
    """Updates platform configuration settings and records audit log event."""
    global _current_settings
    old_data = _current_settings.model_dump()
    _current_settings = new_settings
    updated_data = new_settings.model_dump()

    log_user_action(
        request=request,
        user=user,
        action="admin:settings_update",
        resource="platform_settings",
        result="success",
        payload={
            "old_settings": old_data,
            "new_settings": updated_data,
        },
    )

    return _current_settings
