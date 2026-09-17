"""Audit log routes for Norma BDD Platform FastAPI server."""

from typing import List, Dict, Any
from fastapi import APIRouter
from pydantic import BaseModel

from antinode_norma.governance.audit import AuditLog, AuditRecord

router = APIRouter(prefix="/api/audit", tags=["Audit"])

# Shared in-memory AuditLog instance for server
audit_log = AuditLog()


class AuditIntegrityResponse(BaseModel):
    is_valid: bool
    record_count: int


@router.get("", response_model=List[AuditRecord])
async def list_audit_records() -> List[AuditRecord]:
    """Lists all audit log records."""
    return audit_log.records


@router.get("/verify", response_model=AuditIntegrityResponse)
async def verify_audit_integrity() -> AuditIntegrityResponse:
    """Verifies the SHA-256 hash chain integrity of the audit trail."""
    valid = audit_log.verify_integrity()
    return AuditIntegrityResponse(
        is_valid=valid,
        record_count=len(audit_log.records),
    )
