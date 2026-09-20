import pytest
from antinode_norma.delivery.xray import XrayDeliveryAdapter
from antinode_norma.governance.approval import ApprovalGate


def test_deliver_feature_xray_test_mode():
    adapter = XrayDeliveryAdapter()
    gherkin = """
    Feature: Checkout

      Scenario: Valid checkout
        Given items in cart
        When checkout is completed
        Then order is confirmed
    """
    report = adapter.deliver_feature(
        feature_id="FEAT-XRAY-101",
        gherkin_text=gherkin,
        project_key="PROJ",
        test_mode=True,
    )
    assert report.status == "SUCCESS"
    assert report.delivered_count == 1
    assert report.test_mode is True
    assert "Simulated delivery" in report.message


def test_deliver_unapproved_feature_xray_fails():
    approval = ApprovalGate()
    approval.submit_request(feature_id="FEAT-UNAPPROVED", gherkin_text="Feature: Test")

    adapter = XrayDeliveryAdapter(approval_gate=approval)
    with pytest.raises(PermissionError, match="not approved for delivery"):
        adapter.deliver_feature(
            feature_id="FEAT-UNAPPROVED",
            gherkin_text="Feature: Test\nScenario: One",
            project_key="PROJ",
            test_mode=True,
        )


def test_deliver_feature_xray_live_mocked(monkeypatch):
    class MockAuthResponse:
        ok = True
        def json(self): return "mock_token"

    class MockImportResponse:
        ok = True
        def json(self): return {"jobId": "12345"}

    auth_called = False
    import_called = False

    def mock_post(url, json=None, headers=None, files=None, timeout=None):
        nonlocal auth_called, import_called
        if "authenticate" in url:
            auth_called = True
            return MockAuthResponse()
        elif "import/feature" in url:
            import_called = True
            return MockImportResponse()
        raise ValueError(f"Unexpected URL: {url}")

    monkeypatch.setattr("requests.post", mock_post)
    monkeypatch.setenv("XRAY_CLIENT_ID", "dummy_id")
    monkeypatch.setenv("XRAY_CLIENT_SECRET", "dummy_secret")

    adapter = XrayDeliveryAdapter()
    report = adapter.deliver_feature(
        feature_id="FEAT-LIVE-XRAY",
        gherkin_text="Feature: Test\nScenario: Live Scenario",
        project_key="PROJ",
        test_mode=False,
    )

    assert report.status == "SUCCESS"
    assert report.test_mode is False
    assert auth_called is True
    assert import_called is True
