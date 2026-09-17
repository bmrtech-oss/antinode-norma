"""Authentication and Authorization package for Antinode Norma Platform."""

from antinode_norma.auth.middleware import get_current_user, requires_permission
from antinode_norma.auth.models import Role, User
from antinode_norma.auth.oidc import (
    OIDCConfig,
    build_authorization_url,
    generate_pkce_pair,
    map_claims_to_user,
)
from antinode_norma.auth.roles import (
    ADMIN_WRITE,
    APPROVAL_ACTION,
    AUDIT_READ,
    FEATURE_READ,
    FEATURE_WRITE,
    ROLE_PERMISSIONS,
    get_role_permissions,
    get_user_permissions,
    has_permission,
)
from antinode_norma.auth.saml import (
    SAMLConfig,
    build_authn_request,
    generate_sp_metadata,
    parse_saml_response_claims,
)

__all__ = [
    "Role",
    "User",
    "OIDCConfig",
    "build_authorization_url",
    "generate_pkce_pair",
    "map_claims_to_user",
    "SAMLConfig",
    "build_authn_request",
    "generate_sp_metadata",
    "parse_saml_response_claims",
    "get_current_user",
    "requires_permission",
    "FEATURE_READ",
    "FEATURE_WRITE",
    "APPROVAL_ACTION",
    "AUDIT_READ",
    "ADMIN_WRITE",
    "ROLE_PERMISSIONS",
    "get_role_permissions",
    "get_user_permissions",
    "has_permission",
]
