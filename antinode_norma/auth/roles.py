"""Role Permission Matrix for Antinode Norma Platform SSO & RBAC."""

from typing import Set
from antinode_norma.auth.models import Role, User

# Permission constants
FEATURE_READ = "feature:read"
FEATURE_WRITE = "feature:write"
APPROVAL_ACTION = "approval:action"
AUDIT_READ = "audit:read"
ADMIN_WRITE = "admin:write"

ROLE_PERMISSIONS = {
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
    """Returns the set of permissions granted to a given role."""
    return ROLE_PERMISSIONS.get(role, set())


def get_user_permissions(user: User) -> Set[str]:
    """Returns the combined set of permissions granted across all roles assigned to the user."""
    if not user.is_active:
        return set()

    permissions: Set[str] = set()
    for role in user.roles:
        permissions.update(get_role_permissions(role))
    return permissions


def has_permission(user: User, permission: str) -> bool:
    """Checks whether an active user has the specified permission."""
    return permission in get_user_permissions(user)
