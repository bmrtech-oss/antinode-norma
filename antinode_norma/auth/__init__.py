"""Auth package for Antinode Norma Platform."""

from antinode_norma.auth.models import Role, User
from antinode_norma.auth.roles import (
    FEATURE_READ,
    FEATURE_WRITE,
    APPROVAL_ACTION,
    AUDIT_READ,
    ADMIN_WRITE,
    get_role_permissions,
    get_user_permissions,
    has_permission,
)

__all__ = [
    "Role",
    "User",
    "FEATURE_READ",
    "FEATURE_WRITE",
    "APPROVAL_ACTION",
    "AUDIT_READ",
    "ADMIN_WRITE",
    "get_role_permissions",
    "get_user_permissions",
    "has_permission",
]
