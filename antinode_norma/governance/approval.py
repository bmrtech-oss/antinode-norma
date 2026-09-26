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
    owner_id: Optional[str] = None
    tenant_id: Optional[str] = None
    source_job_id: Optional[str] = None
    source_result_id: Optional[str] = None
    reviewer: Optional[str] = None
    reason: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ApprovalGate:
    def __init__(self, audit_log: Optional[AuditLog] = None, database_url: Optional[str] = None):
        self.audit_log = audit_log or AuditLog()
        self.database_url = database_url
        self.requests: Dict[str, ApprovalRequest] = {}
        if database_url:
            from antinode_norma.database import load_approval_requests

            self.requests = {
                item["id"]: ApprovalRequest(**item)
                for item in load_approval_requests(database_url)
            }

    def submit_request(
        self,
        feature_id: str,
        gherkin_text: str,
        requested_by: str = "system",
        source_job_id: Optional[str] = None,
        source_result_id: Optional[str] = None,
        owner_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> ApprovalRequest:
        req = ApprovalRequest(
            feature_id=feature_id,
            gherkin_text=gherkin_text,
            status=ApprovalStatus.PENDING,
            requested_by=requested_by,
            source_job_id=source_job_id,
            source_result_id=source_result_id,
            owner_id=owner_id,
            tenant_id=tenant_id,
        )
        self.requests[req.id] = req
        self._persist(req)
        self.audit_log.record_event(
            action="approval_submitted",
            resource=feature_id,
            actor=requested_by,
            payload={"request_id": req.id, "status": req.status.value,
                     "owner_id": owner_id, "tenant_id": tenant_id},
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
        self._persist(req)

        self.audit_log.record_event(
            action="approval_approved",
            resource=req.feature_id,
            actor=reviewer,
            payload={"request_id": req.id, "status": req.status.value,
                     "owner_id": req.owner_id, "tenant_id": req.tenant_id},
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
        self._persist(req)

        self.audit_log.record_event(
            action="approval_rejected",
            resource=req.feature_id,
            actor=reviewer,
            payload={"request_id": req.id, "status": req.status.value,
                     "owner_id": req.owner_id, "tenant_id": req.tenant_id},
        )
        return req

    def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        return self.requests.get(request_id)

    def is_approved(self, feature_id: str) -> bool:
        for req in self.requests.values():
            if req.feature_id == feature_id and req.status == ApprovalStatus.APPROVED:
                return True
        return False

    def _persist(self, request: ApprovalRequest) -> None:
        if self.database_url:
            from antinode_norma.database import save_approval_request

            save_approval_request(self.database_url, request.model_dump())
