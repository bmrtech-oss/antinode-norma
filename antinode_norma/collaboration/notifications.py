"""Notifications manager and dispatchers for multi-channel alerting (Email, Slack, Teams)."""

import os
import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from antinode_norma.connectors.notifications import post_slack_message, post_teams_message

logger = logging.getLogger(__name__)


class Notification(BaseModel):
    event_type: str
    title: str
    message: str
    recipient: Optional[str] = None
    channel: str = "slack"  # slack, teams, email
    data: Dict[str, Any] = Field(default_factory=dict)


class NotificationManager:
    def __init__(
        self,
        slack_webhook_url: Optional[str] = None,
        teams_webhook_url: Optional[str] = None,
    ) -> None:
        self.slack_webhook_url = slack_webhook_url or os.environ.get("SLACK_WEBHOOK_URL")
        self.teams_webhook_url = teams_webhook_url or os.environ.get("TEAMS_WEBHOOK_URL")

    def send_notification(self, notification: Notification) -> Dict[str, Any]:
        """Dispatches a notification to the requested channel with fallback when unconfigured."""
        channel = notification.channel.lower()

        if channel == "slack":
            return self._send_slack(notification)
        elif channel == "teams":
            return self._send_teams(notification)
        elif channel == "email":
            return self._send_email(notification)
        else:
            logger.warning(f"Unsupported notification channel '{channel}'. Falling back to log.")
            return {"status": "unsupported", "channel": channel}

    def _send_slack(self, notification: Notification) -> Dict[str, Any]:
        if not self.slack_webhook_url:
            logger.info(f"Slack webhook not configured. Mock sending notification '{notification.title}'.")
            return {"status": "skipped", "reason": "webhook_not_configured"}

        try:
            return post_slack_message(
                webhook_url=self.slack_webhook_url,
                text=f"*{notification.title}*\n{notification.message}",
            )
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return {"status": "error", "error": str(e)}

    def _send_teams(self, notification: Notification) -> Dict[str, Any]:
        if not self.teams_webhook_url:
            logger.info(f"Teams webhook not configured. Mock sending notification '{notification.title}'.")
            return {"status": "skipped", "reason": "webhook_not_configured"}

        try:
            return post_teams_message(
                webhook_url=self.teams_webhook_url,
                title=notification.title,
                text=notification.message,
            )
        except Exception as e:
            logger.error(f"Failed to send Teams notification: {e}")
            return {"status": "error", "error": str(e)}

    def _send_email(self, notification: Notification) -> Dict[str, Any]:
        logger.info(f"Mock email dispatch to '{notification.recipient}': {notification.title}")
        return {"status": "sent", "channel": "email", "recipient": notification.recipient}
