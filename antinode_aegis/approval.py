"""Tenant-aware Aegis approval workflow backed by the audit ledger."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from .audit import AuditLedger


class ApprovalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ApprovalRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    feature_id: str
    requested_by: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    reviewer_id: Optional[str] = None
    reason: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ApprovalWorkflow:
    """In-memory request index with durable audit events."""

    def __init__(self, audit: Optional[AuditLedger] = None):
        self.audit = audit or AuditLedger()
        self.requests: Dict[str, ApprovalRequest] = {}

    def submit(self, *, tenant_id: str, feature_id: str, requested_by: str) -> ApprovalRequest:
        request = ApprovalRequest(
            tenant_id=tenant_id,
            feature_id=feature_id,
            requested_by=requested_by,
        )
        self.requests[request.request_id] = request
        self.audit.append(
            tenant_id=tenant_id,
            actor_id=requested_by,
            action="approval.requested",
            resource_type="approval_request",
            resource_id=request.request_id,
            metadata={"feature_id": feature_id, "status": request.status.value},
        )
        return request

    def approve(self, request_id: str, *, reviewer_id: str, reason: Optional[str] = None) -> ApprovalRequest:
        return self._transition(
            request_id,
            status=ApprovalStatus.APPROVED,
            reviewer_id=reviewer_id,
            reason=reason,
            action="approval.approved",
        )

    def reject(self, request_id: str, *, reviewer_id: str, reason: str) -> ApprovalRequest:
        return self._transition(
            request_id,
            status=ApprovalStatus.REJECTED,
            reviewer_id=reviewer_id,
            reason=reason,
            action="approval.rejected",
        )

    def _transition(
        self,
        request_id: str,
        *,
        status: ApprovalStatus,
        reviewer_id: str,
        reason: Optional[str],
        action: str,
    ) -> ApprovalRequest:
        if request_id not in self.requests:
            raise KeyError(f"Approval request {request_id} not found")
        request = self.requests[request_id]
        if request.status is not ApprovalStatus.PENDING:
            raise ValueError(f"Cannot transition request in {request.status.value} state")

        request.status = status
        request.reviewer_id = reviewer_id
        request.reason = reason
        request.updated_at = datetime.now(timezone.utc).isoformat()
        self.audit.append(
            tenant_id=request.tenant_id,
            actor_id=reviewer_id,
            action=action,
            resource_type="approval_request",
            resource_id=request.request_id,
            metadata={"feature_id": request.feature_id, "status": status.value, "reason": reason},
        )
        return request

    def get(self, request_id: str) -> Optional[ApprovalRequest]:
        return self.requests.get(request_id)

    def is_approved(self, *, tenant_id: str, feature_id: str) -> bool:
        return any(
            request.tenant_id == tenant_id
            and request.feature_id == feature_id
            and request.status is ApprovalStatus.APPROVED
            for request in self.requests.values()
        )
