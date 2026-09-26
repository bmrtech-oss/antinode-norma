"""Unit tests for AUTH-0-T08: Authentik group and claim-to-Norma-role mapping."""

from antinode_norma.auth.models import Role
from antinode_norma.auth.oidc import map_claims_to_roles, map_claims_to_user


def test_map_admin_group_claim():
    claims = {"sub": "user1", "email": "admin@example.com", "groups": ["norma-admin"]}
    roles = map_claims_to_roles(claims)
    assert roles == [Role.ADMIN]

    user = map_claims_to_user(claims)
    assert user.roles == [Role.ADMIN]


def test_map_reviewer_group_claim():
    claims = {"sub": "user2", "groups": ["norma-reviewer"]}
    roles = map_claims_to_roles(claims)
    assert roles == [Role.REVIEWER]


def test_map_generator_group_claim():
    claims = {"sub": "user3", "groups": ["norma-generator"]}
    roles = map_claims_to_roles(claims)
    assert roles == [Role.GENERATOR]


def test_map_viewer_group_claim():
    claims = {"sub": "user4", "groups": ["norma-viewer"]}
    roles = map_claims_to_roles(claims)
    assert roles == [Role.VIEWER]


def test_map_multiple_role_groups():
    claims = {"sub": "user5", "groups": ["norma-generator", "norma-reviewer"]}
    roles = map_claims_to_roles(claims)
    assert set(roles) == {Role.GENERATOR, Role.REVIEWER}


def test_unmapped_groups_default_to_least_privilege_viewer():
    claims = {"sub": "user6", "groups": ["engineering", "unknown_group"]}
    roles = map_claims_to_roles(claims)
    assert roles == [Role.VIEWER]

    user = map_claims_to_user(claims)
    assert user.roles == [Role.VIEWER]


def test_empty_claims_default_to_viewer():
    claims = {"sub": "user7"}
    roles = map_claims_to_roles(claims)
    assert roles == [Role.VIEWER]


def test_alternate_roles_claims_and_realm_access():
    claims_roles = {"sub": "user8", "roles": ["admin"]}
    assert map_claims_to_roles(claims_roles) == [Role.ADMIN]

    claims_norma_roles = {"sub": "user9", "norma_roles": ["reviewer"]}
    assert map_claims_to_roles(claims_norma_roles) == [Role.REVIEWER]

    claims_realm_access = {"sub": "user10", "realm_access": {"roles": ["generator"]}}
    assert map_claims_to_roles(claims_realm_access) == [Role.GENERATOR]


def test_disabled_user_claim_handling():
    active_user_claims = {"sub": "user11", "groups": ["norma-admin"], "active": True}
    user_active = map_claims_to_user(active_user_claims)
    assert user_active.is_active is True

    inactive_active_claim = {"sub": "user12", "groups": ["norma-admin"], "active": False}
    user_inactive1 = map_claims_to_user(inactive_active_claim)
    assert user_inactive1.is_active is False

    inactive_enabled_claim = {"sub": "user13", "groups": ["norma-admin"], "enabled": False}
    user_inactive2 = map_claims_to_user(inactive_enabled_claim)
    assert user_inactive2.is_active is False
