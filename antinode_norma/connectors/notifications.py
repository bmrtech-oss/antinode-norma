import os
from typing import Dict, Any, Optional

import requests


def post_slack_message(webhook_url: str, text: str, blocks: Optional[Any] = None) -> Dict[str, Any]:
    if not webhook_url or not text:
        raise ValueError("webhook_url and text are required for Slack notifications.")
    payload: Dict[str, Any] = {"text": text}
    if blocks is not None:
        payload["blocks"] = blocks
    response = requests.post(webhook_url, json=payload, timeout=15)
    response.raise_for_status()
    return {"status": "sent", "response_code": response.status_code, "body": response.text}


def post_teams_message(webhook_url: str, title: str, text: str) -> Dict[str, Any]:
    if not webhook_url or not title or not text:
        raise ValueError("webhook_url, title and text are required for Teams notifications.")
    payload = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "themeColor": "0076D7",
        "summary": title,
        "sections": [{"activityTitle": title, "text": text}],
    }
    response = requests.post(webhook_url, json=payload, timeout=15)
    response.raise_for_status()
    return {"status": "sent", "response_code": response.status_code, "body": response.text}
