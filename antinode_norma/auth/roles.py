"""Role permission matrix and permission resolution helpers."""

from typing import Dict, Set
from antinode_norma.auth.models import Role, User

# Permission constants
FEATURE_READ = "features:read"
FEATURE_WRITE = "features:generate"
APPROVAL_ACTION = "features:approve"
AUDIT_READ = "audit:read"
ADMIN_WRITE = "settings:manage"

# Role permission matrix
ROLE_PERMISSIONS: Dict[Role, Set[str]] = {
    Role.ADMIN: {
        FEATURE_READ,
        FEATURE_WRITE,
        APPROVAL_ACTION,
        AUDIT_READ,
        ADMIN_WRITE,
    },
    Role.REVIEWER: {
        FEATURE_READ,
        APPROVAL_ACTION,
        AUDIT_READ,
    },
    Role.GENERATOR: {
        FEATURE_READ,
        FEATURE_WRITE,
        AUDIT_READ,
    },
    Role.VIEWER: {
        FEATURE_READ,
        AUDIT_READ,
    },
}


def get_role_permissions(role: Role) -> Set[str]:
    """Get permission set for a given Role."""
    return ROLE_PERMISSIONS.get(role, set())


def get_user_permissions(user: User) -> Set[str]:
    """Resolve aggregate permissions across all roles assigned to an active user."""
    if not user.is_active:
        return set()

    permissions: Set[str] = set()
    for role in user.roles:
        permissions.update(get_role_permissions(role))
    return permissions


def has_permission(user: User, permission: str) -> bool:
    """Check if an active user possesses a specific permission."""
    if not user.is_active:
        return False
    return permission in get_user_permissions(user)
