"""Unit tests for Phase 10 Task P10-T01: User and Role Model & Permission Matrix."""

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


def test_user_default_role():
    user = User(username="johndoe", email="john@example.com")
    assert user.roles == [Role.VIEWER]
    assert user.is_active is True


def test_viewer_role_permissions():
    user = User(username="viewer_user", email="viewer@example.com", roles=[Role.VIEWER])
    perms = get_user_permissions(user)

    assert FEATURE_READ in perms
    assert AUDIT_READ in perms
    assert FEATURE_WRITE not in perms
    assert APPROVAL_ACTION not in perms
    assert ADMIN_WRITE not in perms

    assert has_permission(user, FEATURE_READ) is True
    assert has_permission(user, APPROVAL_ACTION) is False


def test_generator_role_permissions():
    user = User(username="gen_user", email="gen@example.com", roles=[Role.GENERATOR])
    perms = get_user_permissions(user)

    assert FEATURE_READ in perms
    assert FEATURE_WRITE in perms
    assert AUDIT_READ in perms
    assert APPROVAL_ACTION not in perms


def test_reviewer_role_permissions():
    user = User(username="rev_user", email="rev@example.com", roles=[Role.REVIEWER])
    perms = get_user_permissions(user)

    assert FEATURE_READ in perms
    assert APPROVAL_ACTION in perms
    assert AUDIT_READ in perms
    assert FEATURE_WRITE not in perms


def test_admin_role_permissions():
    user = User(username="admin_user", email="admin@example.com", roles=[Role.ADMIN])
    perms = get_user_permissions(user)

    assert FEATURE_READ in perms
    assert FEATURE_WRITE in perms
    assert APPROVAL_ACTION in perms
    assert AUDIT_READ in perms
    assert ADMIN_WRITE in perms


def test_inactive_user_has_no_permissions():
    user = User(
        username="inactive_user",
        email="inactive@example.com",
        roles=[Role.ADMIN],
        is_active=False,
    )
    assert get_user_permissions(user) == set()
    assert has_permission(user, ADMIN_WRITE) is False
