"""A2 TestRail delivery adapter."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel

from antinode_norma.connectors.testrail_connector import add_test_case

from .approval import ApprovalWorkflow


class TestRailReport(BaseModel):
    tenant_id: str
    feature_id: str
    project_id: int
    delivered_count: int
    case_ids: List[int] = []
    test_mode: bool = True


class TestRailAdapter:
    __test__ = False

    def __init__(self, approvals: Optional[ApprovalWorkflow] = None):
        self.approvals = approvals

    def deliver(
        self,
        *,
        tenant_id: str,
        feature_id: str,
        gherkin_text: str,
        project_id: int,
        test_mode: bool = True,
    ) -> TestRailReport:
        if self.approvals and not self.approvals.is_approved(tenant_id=tenant_id, feature_id=feature_id):
            raise PermissionError(f"Feature '{feature_id}' is not approved for delivery.")

        scenarios = [
            line.strip().split(":", 1)[1].strip()
            for line in gherkin_text.splitlines()
            if line.strip().startswith(("Scenario:", "Scenario Outline:"))
        ]
        case_ids: List[int] = []
        for index, title in enumerate(scenarios, start=1):
            if test_mode:
                case_ids.append(8000 + index)
            else:
                case_ids.append(
                    add_test_case(section_id=project_id, title=title, description=gherkin_text).get("id", index)
                )

        return TestRailReport(
            tenant_id=tenant_id,
            feature_id=feature_id,
            project_id=project_id,
            delivered_count=len(case_ids),
            case_ids=case_ids,
            test_mode=test_mode,
        )
