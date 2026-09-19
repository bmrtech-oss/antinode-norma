"""Unit tests for Phase 11 Task P11-T05: Notifications."""

from fastapi.testclient import TestClient

from antinode_norma.collaboration import Notification, NotificationManager
from antinode_norma.server.api import app


def test_notification_manager_unconfigured_webhooks():
    manager = NotificationManager()

    slack_notif = Notification(
        event_type="approval_requested",
        title="Approval Needed",
        message="Feature login.feature requires review",
        channel="slack",
    )
    res_slack = manager.send_notification(slack_notif)
    assert res_slack["status"] == "skipped"

    teams_notif = Notification(
        event_type="feature_approved",
        title="Feature Approved",
        message="Feature checkout.feature approved",
        channel="teams",
    )
    res_teams = manager.send_notification(teams_notif)
    assert res_teams["status"] == "skipped"

    email_notif = Notification(
        event_type="comment_added",
        title="New Comment",
        message="Mentioned in comment",
        recipient="lead@norma.local",
        channel="email",
    )
    res_email = manager.send_notification(email_notif)
    assert res_email["status"] == "sent"
    assert res_email["recipient"] == "lead@norma.local"


def test_notifications_api_endpoint():
    client = TestClient(app, headers={"X-User-ID": "test_user"})

    res = client.post(
        "/api/notifications/send",
        json={
            "event_type": "test_alert",
            "title": "Unit Test Alert",
            "message": "Testing notification endpoint",
            "channel": "email",
            "recipient": "qa@norma.local",
        },
    )

    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "sent"
    assert data["channel"] == "email"
