"""Analytics routes for Norma BDD Platform FastAPI server."""

from fastapi import APIRouter, Depends

from antinode_norma.analytics.metrics import AnalyticsCollector, AnalyticsSummary
from antinode_norma.auth.middleware import requires_permission
from antinode_norma.auth.roles import FEATURE_READ
from antinode_norma.server.routes.approvals import gate as _approval_gate
from antinode_norma.server.routes.audit import audit_log as _audit_log
from antinode_norma.server.routes.features import _get_feature_dir

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get(
    "/summary",
    response_model=AnalyticsSummary,
    dependencies=[Depends(requires_permission(FEATURE_READ))],
)
async def get_analytics_summary() -> AnalyticsSummary:
    """Returns aggregated platform KPI metrics and trend analytics."""
    feature_dir = _get_feature_dir()
    feature_count = 0
    if feature_dir.exists() and feature_dir.is_dir():
        feature_count = len(list(feature_dir.glob("*.feature")))

    collector = AnalyticsCollector(
        approval_gate=_approval_gate,
        audit_log=_audit_log,
    )
    return collector.collect_summary(feature_count=feature_count)
