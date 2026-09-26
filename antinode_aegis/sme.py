"""A2 SME review routing queue."""

from __future__ import annotations

from enum import Enum
from typing import Dict, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class ReviewStatus(str, Enum):
    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    RESOLVED = "RESOLVED"


class ReviewRequest(BaseModel):
    review_id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    resource_id: str
    confidence: float
    status: ReviewStatus = ReviewStatus.PENDING
    assigned_to: Optional[str] = None
    resolution: Optional[str] = None


class SMERoutingQueue:
    def __init__(self, assignment_threshold: float = 0.85):
        self.assignment_threshold = assignment_threshold
        self.requests: Dict[str, ReviewRequest] = {}

    def submit(self, *, tenant_id: str, resource_id: str, confidence: float) -> ReviewRequest:
        request = ReviewRequest(
            tenant_id=tenant_id,
            resource_id=resource_id,
            confidence=confidence,
        )
        self.requests[request.review_id] = request
        return request

    def assign(self, review_id: str, *, sme_id: str) -> ReviewRequest:
        request = self._get_pending(review_id)
        if request.confidence >= self.assignment_threshold:
            raise ValueError("High-confidence reviews do not require SME assignment")
        request.status = ReviewStatus.ASSIGNED
        request.assigned_to = sme_id
        return request

    def resolve(self, review_id: str, *, resolution: str) -> ReviewRequest:
        request = self.requests.get(review_id)
        if not request or request.status is not ReviewStatus.ASSIGNED:
            raise ValueError("Only assigned reviews can be resolved")
        request.status = ReviewStatus.RESOLVED
        request.resolution = resolution
        return request

    def _get_pending(self, review_id: str) -> ReviewRequest:
        request = self.requests.get(review_id)
        if not request or request.status is not ReviewStatus.PENDING:
            raise ValueError("Only pending reviews can be assigned")
        return request
