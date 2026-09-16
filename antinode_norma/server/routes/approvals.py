"""Approval queue routes for Norma BDD Platform FastAPI server."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from antinode_norma.governance.approval import ApprovalGate, ApprovalRequest, ApprovalStatus

router = APIRouter(prefix="/api/approvals", tags=["Approvals"])

# Shared in-memory ApprovalGate singleton for the server
gate = ApprovalGate()


class CreateApprovalRequest(BaseModel):
    feature_id: str
    gherkin_text: str = ""
    requested_by: str = "system"


class ActionApprovalPayload(BaseModel):
    reviewer: str = "reviewer"
    reason: Optional[str] = None


@router.get("", response_model=List[ApprovalRequest])
async def list_approvals() -> List[ApprovalRequest]:
    """Lists all approval requests."""
    return list(gate.requests.values())


@router.post("", response_model=ApprovalRequest)
async def create_approval(payload: CreateApprovalRequest) -> ApprovalRequest:
    """Submits a feature for approval."""
    return gate.submit_request(
        feature_id=payload.feature_id,
        gherkin_text=payload.gherkin_text,
        requested_by=payload.requested_by,
    )


@router.post("/{request_id}/approve", response_model=ApprovalRequest)
async def approve_request(request_id: str, payload: ActionApprovalPayload) -> ApprovalRequest:
    """Approves a pending request."""
    try:
        return gate.approve(
            request_id=request_id,
            reviewer=payload.reviewer,
            reason=payload.reason,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Approval request '{request_id}' not found.")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{request_id}/reject", response_model=ApprovalRequest)
async def reject_request(request_id: str, payload: ActionApprovalPayload) -> ApprovalRequest:
    """Rejects a pending request."""
    reason = payload.reason or "Rejected without specified reason"
    try:
        return gate.reject(
            request_id=request_id,
            reviewer=payload.reviewer,
            reason=reason,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Approval request '{request_id}' not found.")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
