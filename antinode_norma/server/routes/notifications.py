"""Notifications routes for Norma BDD Platform FastAPI server."""

from typing import Dict, Any
from fastapi import APIRouter, Depends, Request

from antinode_norma.auth.middleware import log_user_action, requires_permission
from antinode_norma.auth.models import User
from antinode_norma.auth.roles import FEATURE_READ
from antinode_norma.collaboration.notifications import Notification, NotificationManager

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])

notification_manager = NotificationManager()


@router.post(
    "/send",
    response_model=Dict[str, Any],
)
async def send_notification_endpoint(
    request: Request,
    notification: Notification,
    user: User = Depends(requires_permission(FEATURE_READ)),
) -> Dict[str, Any]:
    """Triggers multi-channel event notification dispatch."""
    res = notification_manager.send_notification(notification)

    log_user_action(
        request=request,
        user=user,
        action="notifications:send",
        resource=f"notification:{notification.event_type}",
        result=res.get("status", "unknown"),
        payload={
            "channel": notification.channel,
            "title": notification.title,
            "recipient": notification.recipient,
        },
    )

    return res
