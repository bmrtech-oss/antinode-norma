import pytest
from antinode_norma.delivery.testrail import TestRailDeliveryAdapter
from antinode_norma.governance.approval import ApprovalGate
from antinode_norma.core.types import TestCase


def test_deliver_feature_test_mode():
    adapter = TestRailDeliveryAdapter()
    gherkin = """
    Feature: Payments

      Scenario: Credit card checkout
        Given active card
        When checkout submitted
        Then payment succeeds
    """
    report = adapter.deliver_feature(
        feature_id="FEAT-100",
        gherkin_text=gherkin,
        section_id=42,
        test_mode=True,
    )
    assert report.status == "SUCCESS"
    assert report.delivered_count == 1
    assert report.test_mode is True
    assert report.case_ids == [1001]


def test_deliver_unapproved_feature_fails():
    approval = ApprovalGate()
    approval.submit_request(feature_id="FEAT-UNAPPROVED", gherkin_text="Feature: Test")

    adapter = TestRailDeliveryAdapter(approval_gate=approval)
    with pytest.raises(PermissionError, match="not approved for delivery"):
        adapter.deliver_feature(
            feature_id="FEAT-UNAPPROVED",
            gherkin_text="Feature: Test\nScenario: One",
            section_id=42,
            test_mode=True,
        )


def test_deliver_approved_feature_succeeds():
    approval = ApprovalGate()
    req = approval.submit_request(feature_id="FEAT-APPROVED", gherkin_text="Feature: Test")
    approval.approve(request_id=req.id, reviewer="lead1")

    adapter = TestRailDeliveryAdapter(approval_gate=approval)
    report = adapter.deliver_feature(
        feature_id="FEAT-APPROVED",
        gherkin_text="Feature: Test\nScenario: Approved Scenario",
        section_id=42,
        test_mode=True,
    )
    assert report.status == "SUCCESS"
    assert report.delivered_count == 1


def test_deliver_test_cases_test_mode():
    adapter = TestRailDeliveryAdapter()
    tc1 = TestCase(id="TC-1", title="Transfer test", steps=["Given state", "When action", "Then result"])
    report = adapter.deliver_test_cases(
        feature_id="FEAT-200",
        test_cases=[tc1],
        section_id=10,
        test_mode=True,
    )
    assert report.status == "SUCCESS"
    assert report.delivered_count == 1
    assert report.case_ids == [2001]


def test_deliver_feature_live_mocked(monkeypatch):
    calls = []

    def mock_add_test_case(section_id, title, description=""):
        calls.append((section_id, title, description))
        return {"id": 999}

    monkeypatch.setattr("antinode_norma.delivery.testrail.add_test_case", mock_add_test_case)

    adapter = TestRailDeliveryAdapter()
    gherkin = "Feature: Test\nScenario: Live Scenario"
    report = adapter.deliver_feature(
        feature_id="FEAT-LIVE",
        gherkin_text=gherkin,
        section_id=55,
        test_mode=False,
    )

    assert report.status == "SUCCESS"
    assert report.case_ids == [999]
    assert len(calls) == 1
    assert calls[0][0] == 55
    assert calls[0][1] == "Live Scenario"
