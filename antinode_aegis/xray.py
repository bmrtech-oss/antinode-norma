"""A2 Xray REST delivery adapter."""

from __future__ import annotations

import os
from typing import Optional

import requests
from pydantic import BaseModel

from .approval import ApprovalWorkflow


class XrayReport(BaseModel):
    tenant_id: str
    feature_id: str
    project_key: str
    delivered_count: int
    test_mode: bool = True


class XrayAdapter:
    __test__ = False

    def __init__(self, approvals: Optional[ApprovalWorkflow] = None):
        self.approvals = approvals

    def deliver(
        self,
        *,
        tenant_id: str,
        feature_id: str,
        gherkin_text: str,
        project_key: str,
        test_mode: bool = True,
    ) -> XrayReport:
        if self.approvals and not self.approvals.is_approved(tenant_id=tenant_id, feature_id=feature_id):
            raise PermissionError(f"Feature '{feature_id}' is not approved for delivery.")

        count = sum(
            1
            for line in gherkin_text.splitlines()
            if line.strip().startswith(("Scenario:", "Scenario Outline:"))
        )
        if test_mode:
            return XrayReport(
                tenant_id=tenant_id,
                feature_id=feature_id,
                project_key=project_key,
                delivered_count=count,
                test_mode=True,
            )

        base_url = os.getenv("XRAY_BASE_URL", "https://xray.cloud.getxray.app").rstrip("/")
        client_id = os.getenv("XRAY_CLIENT_ID")
        client_secret = os.getenv("XRAY_CLIENT_SECRET")
        if not client_id or not client_secret:
            raise EnvironmentError("XRAY_CLIENT_ID and XRAY_CLIENT_SECRET must be set for live delivery.")

        auth = requests.post(
            f"{base_url}/api/v2/authenticate",
            json={"client_id": client_id, "client_secret": client_secret},
            timeout=30,
        )
        auth.raise_for_status()
        token = auth.json() if isinstance(auth.json(), str) else auth.text.strip('"')
        response = requests.post(
            f"{base_url}/api/v2/import/feature?projectKey={project_key}",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("feature.feature", gherkin_text, "text/plain")},
            timeout=30,
        )
        response.raise_for_status()
        return XrayReport(
            tenant_id=tenant_id,
            feature_id=feature_id,
            project_key=project_key,
            delivered_count=count,
            test_mode=False,
        )
