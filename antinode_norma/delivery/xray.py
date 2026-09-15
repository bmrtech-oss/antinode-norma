import os
import requests
from typing import Optional
from pydantic import BaseModel
from antinode_norma.governance.approval import ApprovalGate


class XrayDeliveryReport(BaseModel):
    feature_id: str
    project_key: str
    delivered_count: int = 0
    test_mode: bool = True
    status: str = "SUCCESS"
    message: str = ""


class XrayDeliveryAdapter:
    def __init__(self, approval_gate: Optional[ApprovalGate] = None):
        self.approval_gate = approval_gate

    def _verify_approval(self, feature_id: str) -> None:
        if self.approval_gate:
            if not self.approval_gate.is_approved(feature_id):
                raise PermissionError(
                    f"Feature '{feature_id}' is not approved for delivery."
                )

    def deliver_feature(
        self,
        feature_id: str,
        gherkin_text: str,
        project_key: str,
        test_mode: bool = True,
    ) -> XrayDeliveryReport:
        self._verify_approval(feature_id)

        scenarios = []
        for line in gherkin_text.splitlines():
            stripped = line.strip()
            if stripped.startswith("Scenario:") or stripped.startswith("Scenario Outline:"):
                title = stripped.split(":", 1)[1].strip()
                scenarios.append(title)

        scenario_count = len(scenarios) if scenarios else 1

        if test_mode:
            return XrayDeliveryReport(
                feature_id=feature_id,
                project_key=project_key,
                delivered_count=scenario_count,
                test_mode=True,
                status="SUCCESS",
                message=f"Simulated delivery of {scenario_count} scenarios for feature '{feature_id}' to Xray project '{project_key}'.",
            )

        xray_base_url = os.getenv("XRAY_BASE_URL", "https://xray.cloud.getxray.app")
        client_id = os.getenv("XRAY_CLIENT_ID")
        client_secret = os.getenv("XRAY_CLIENT_SECRET")

        if not client_id or not client_secret:
            raise EnvironmentError("XRAY_CLIENT_ID and XRAY_CLIENT_SECRET must be set for live Xray delivery.")

        # Auth request to obtain token
        auth_url = f"{xray_base_url.rstrip('/')}/api/v2/authenticate"
        auth_resp = requests.post(auth_url, json={"client_id": client_id, "client_secret": client_secret}, timeout=30)
        if not auth_resp.ok:
            raise RuntimeError(f"Xray authentication failed: {auth_resp.text}")

        token = auth_resp.json() if isinstance(auth_resp.json(), str) else auth_resp.text.strip('"')

        # Import feature file request
        import_url = f"{xray_base_url.rstrip('/')}/api/v2/import/feature?projectKey={project_key}"
        files = {"file": ("feature.feature", gherkin_text, "text/plain")}
        resp = requests.post(import_url, headers={"Authorization": f"Bearer {token}"}, files=files, timeout=30)

        if not resp.ok:
            raise RuntimeError(f"Xray feature import failed: {resp.text}")

        return XrayDeliveryReport(
            feature_id=feature_id,
            project_key=project_key,
            delivered_count=scenario_count,
            test_mode=False,
            status="SUCCESS",
            message=f"Imported feature '{feature_id}' into Xray project '{project_key}'.",
        )
