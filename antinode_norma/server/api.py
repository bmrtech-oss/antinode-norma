"""FastAPI application server foundation for Norma BDD Platform."""

from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from antinode_norma.server.schemas import HealthResponse, ErrorResponse
from antinode_norma.server.routes import (
    features_router,
    approvals_router,
    audit_router,
    traceability_router,
    dashboard_router,
    auth_router,
)

app = FastAPI(
    title="Norma BDD Platform API",
    description="Enterprise BDD Feature Generation, Quality Gates, Governance, and Execution Platform API",
    version="0.1.0",
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


# Register route modules
app.include_router(features_router)
app.include_router(approvals_router)
app.include_router(audit_router)
app.include_router(traceability_router)
app.include_router(dashboard_router)
app.include_router(auth_router)


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint returning API operational status."""
    return HealthResponse(status="ok", version="0.1.0")


# Mount static SPA if built dist exists
static_dir = Path("ui/dist")
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static_spa")
