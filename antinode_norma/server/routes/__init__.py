"""Server routes package for Antinode Norma."""

from antinode_norma.server.routes.features import router as features_router
from antinode_norma.server.routes.approvals import router as approvals_router
from antinode_norma.server.routes.audit import router as audit_router
from antinode_norma.server.routes.traceability import router as traceability_router
from antinode_norma.server.routes.dashboard import dashboard_router
from antinode_norma.server.routes.auth import router as auth_router
from antinode_norma.server.routes.admin import router as admin_router
from antinode_norma.server.routes.comments import router as comments_router
from antinode_norma.server.routes.notifications import router as notifications_router
from antinode_norma.server.routes.analytics import router as analytics_router
from antinode_norma.server.routes.imports import (
    router as imports_router, generation_router, legacy_generation_router,
)

__all__ = [
    "features_router",
    "approvals_router",
    "audit_router",
    "traceability_router",
    "dashboard_router",
    "auth_router",
    "admin_router",
    "comments_router",
    "notifications_router",
    "analytics_router",
    "imports_router",
    "generation_router",
    "legacy_generation_router",
]
