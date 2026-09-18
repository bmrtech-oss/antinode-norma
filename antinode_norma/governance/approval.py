import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Optional
from pydantic import BaseModel, Field
from antinode_norma.governance.audit import AuditLog


class ApprovalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ApprovalRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    feature_id: str
    gherkin_text: str = ""
    status: ApprovalStatus = ApprovalStatus.PENDING
    requested_by: str = "system"
    reviewer: Optional[str] = None
    reason: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ApprovalGate:
    def __init__(self, audit_log: Optional[AuditLog] = None):
        self.audit_log = audit_log or AuditLog()
        self.requests: Dict[str, ApprovalRequest] = {}

    def submit_request(self, feature_id: str, gherkin_text: str, requested_by: str = "system") -> ApprovalRequest:
        req = ApprovalRequest(
            feature_id=feature_id,
            gherkin_text=gherkin_text,
            status=ApprovalStatus.PENDING,
            requested_by=requested_by,
        )
        self.requests[req.id] = req
        self.audit_log.record_event(
            action="approval_submitted",
            resource=feature_id,
            actor=requested_by,
            payload={"request_id": req.id, "status": req.status.value},
        )
        return req

    def approve(self, request_id: str, reviewer: str, reason: Optional[str] = None) -> ApprovalRequest:
        if request_id not in self.requests:
            raise KeyError(f"Approval request {request_id} not found")

        req = self.requests[request_id]
        if req.status != ApprovalStatus.PENDING:
            raise ValueError(f"Cannot approve request in {req.status.value} state")

        req.status = ApprovalStatus.APPROVED
        req.reviewer = reviewer
        req.reason = reason
        req.updated_at = datetime.now(timezone.utc).isoformat()

        self.audit_log.record_event(
            action="approval_approved",
            resource=req.feature_id,
            actor=reviewer,
            payload={"request_id": req.id, "reason": reason, "status": req.status.value},
        )
        return req

    def reject(self, request_id: str, reviewer: str, reason: str) -> ApprovalRequest:
        if request_id not in self.requests:
            raise KeyError(f"Approval request {request_id} not found")

        req = self.requests[request_id]
        if req.status != ApprovalStatus.PENDING:
            raise ValueError(f"Cannot reject request in {req.status.value} state")

        req.status = ApprovalStatus.REJECTED
        req.reviewer = reviewer
        req.reason = reason
        req.updated_at = datetime.now(timezone.utc).isoformat()

        self.audit_log.record_event(
            action="approval_rejected",
            resource=req.feature_id,
            actor=reviewer,
            payload={"request_id": req.id, "reason": reason, "status": req.status.value},
        )
        return req

    def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        return self.requests.get(request_id)

    def is_approved(self, feature_id: str) -> bool:
        for req in self.requests.values():
            if req.feature_id == feature_id and req.status == ApprovalStatus.APPROVED:
                return True
        return False
