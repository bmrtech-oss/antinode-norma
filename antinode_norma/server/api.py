"""FastAPI application server foundation for Norma BDD Platform."""

from pathlib import Path
from fastapi import FastAPI, APIRouter, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from antinode_norma.server.schemas import HealthResponse, ErrorResponse
from antinode_norma.utils.observability import get_health_status, metrics_registry
from antinode_norma.server.routes import (
    features_router,
    approvals_router,
    audit_router,
    traceability_router,
    dashboard_router,
    auth_router,
    admin_router,
    comments_router,
    notifications_router,
    analytics_router,
    imports_router,
    generation_router,
    legacy_generation_router,
)

app = FastAPI(
    title="Norma BDD Platform API",
    description="Enterprise BDD Feature Generation, Quality Gates, Governance, and Execution Platform API",
    version="0.1.0-alpha",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(detail=str(exc.detail)).model_dump(),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(detail="Internal Server Error", error_code="INTERNAL_ERROR").model_dump(),
    )


v1_router = APIRouter(prefix="/v1")
v1_router.include_router(features_router)
v1_router.include_router(approvals_router)
v1_router.include_router(audit_router)
v1_router.include_router(traceability_router)
v1_router.include_router(dashboard_router)
v1_router.include_router(auth_router)
v1_router.include_router(admin_router)
v1_router.include_router(comments_router)
v1_router.include_router(notifications_router)
v1_router.include_router(analytics_router)
v1_router.include_router(imports_router)
v1_router.include_router(generation_router)
v1_router.include_router(legacy_generation_router, prefix="/api")
# Preserve the initial Phase 1 paths while exposing the public contracts above.
v1_router.include_router(imports_router, prefix="/api")
v1_router.include_router(generation_router, prefix="/api")

# Mount /v1/ versioned router and legacy unversioned aliases
app.include_router(v1_router)

app.include_router(features_router)
app.include_router(approvals_router)
app.include_router(audit_router)
app.include_router(traceability_router)
app.include_router(dashboard_router)
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(comments_router)
app.include_router(notifications_router)
app.include_router(analytics_router)
app.include_router(imports_router, prefix="/api")
app.include_router(generation_router, prefix="/api")
app.include_router(legacy_generation_router, prefix="/api")


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint returning API operational status."""
    status_info = get_health_status()
    return HealthResponse(status=status_info["status"], version=status_info["version"])


@app.get("/metrics", tags=["Observability"])
async def prometheus_metrics():
    """Returns Prometheus metrics in text format."""
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(metrics_registry.get_prometheus_metrics())


# Mount static SPA if built dist exists
static_dir = Path("ui/dist")
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static_spa")
