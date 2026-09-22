"""Approval queue routes for Norma BDD Platform FastAPI server."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from antinode_norma.auth.middleware import ensure_resource_owner, requires_permission
from antinode_norma.auth.roles import APPROVAL_ACTION, FEATURE_READ
from antinode_norma.auth.models import Role, User
from antinode_norma.governance.approval import ApprovalGate, ApprovalRequest

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


@router.get("", response_model=List[ApprovalRequest], dependencies=[Depends(requires_permission(FEATURE_READ))])
async def list_approvals(user: User = Depends(requires_permission(FEATURE_READ))) -> List[ApprovalRequest]:
    """Lists all approval requests."""
    return [item for item in gate.requests.values()
            if (item.tenant_id in (None, user.tenant_id or "default")
                and (item.owner_id in (None, user.id) or Role.ADMIN in user.roles))]


@router.post("", response_model=ApprovalRequest, dependencies=[Depends(requires_permission(APPROVAL_ACTION))])
async def create_approval(payload: CreateApprovalRequest, user: User = Depends(requires_permission(APPROVAL_ACTION))) -> ApprovalRequest:
    """Submits a feature for approval."""
    return gate.submit_request(
        feature_id=payload.feature_id,
        gherkin_text=payload.gherkin_text,
        requested_by=payload.requested_by,
        owner_id=user.id, tenant_id=user.tenant_id or "default",
    )


@router.post("/{request_id}/approve", response_model=ApprovalRequest, dependencies=[Depends(requires_permission(APPROVAL_ACTION))])
async def approve_request(request_id: str, payload: ActionApprovalPayload, user: User = Depends(requires_permission(APPROVAL_ACTION))) -> ApprovalRequest:
    """Approves a pending request."""
    try:
        request = gate.get_request(request_id)
        if request is not None:
            ensure_resource_owner(user, request.model_dump())
        return gate.approve(
            request_id=request_id,
            reviewer=payload.reviewer,
            reason=payload.reason,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Approval request '{request_id}' not found.")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{request_id}/reject", response_model=ApprovalRequest, dependencies=[Depends(requires_permission(APPROVAL_ACTION))])
async def reject_request(request_id: str, payload: ActionApprovalPayload, user: User = Depends(requires_permission(APPROVAL_ACTION))) -> ApprovalRequest:
    """Rejects a pending request."""
    reason = payload.reason or "Rejected without specified reason"
    request = gate.get_request(request_id)
    if request is not None:
        ensure_resource_owner(user, request.model_dump())
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
