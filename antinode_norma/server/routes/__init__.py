"""Server routes package for Antinode Norma."""

from antinode_norma.server.routes.features import router as features_router
from antinode_norma.server.routes.approvals import router as approvals_router
from antinode_norma.server.routes.audit import router as audit_router
from antinode_norma.server.routes.traceability import router as traceability_router

__all__ = ["features_router", "approvals_router", "audit_router", "traceability_router"]
