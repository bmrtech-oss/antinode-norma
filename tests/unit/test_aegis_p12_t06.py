import pytest

from antinode_aegis.sme import ReviewStatus, SMERoutingQueue


def test_low_confidence_review_routes_and_resolves():
    queue = SMERoutingQueue(assignment_threshold=0.85)
    request = queue.submit(tenant_id="tenant-1", resource_id="FEAT-1206", confidence=0.62)

    assigned = queue.assign(request.review_id, sme_id="sme-1")
    assigned_status = assigned.status
    assigned_to = assigned.assigned_to
    resolved = queue.resolve(request.review_id, resolution="Approved after review")

    assert assigned_status is ReviewStatus.ASSIGNED
    assert assigned_to == "sme-1"
    assert resolved.status is ReviewStatus.RESOLVED
    assert resolved.resolution == "Approved after review"


def test_high_confidence_review_does_not_route():
    queue = SMERoutingQueue()
    request = queue.submit(tenant_id="tenant-1", resource_id="FEAT-1207", confidence=0.96)

    with pytest.raises(ValueError, match="do not require SME"):
        queue.assign(request.review_id, sme_id="sme-1")
