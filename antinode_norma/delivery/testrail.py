from typing import List, Optional
from pydantic import BaseModel, Field
from antinode_norma.core.types import TestCase
from antinode_norma.governance.approval import ApprovalGate
from antinode_norma.connectors.testrail_connector import add_test_case


class DeliveryReport(BaseModel):
    feature_id: str
    section_id: int
    delivered_count: int = 0
    case_ids: List[int] = Field(default_factory=list)
    test_mode: bool = True
    status: str = "SUCCESS"
    message: str = ""


class TestRailDeliveryAdapter:
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
        section_id: int,
        test_mode: bool = True,
    ) -> DeliveryReport:
        self._verify_approval(feature_id)

        scenarios = []
        for line in gherkin_text.splitlines():
            stripped = line.strip()
            if stripped.startswith("Scenario:") or stripped.startswith("Scenario Outline:"):
                title = stripped.split(":", 1)[1].strip()
                scenarios.append(title)

        if not scenarios:
            return DeliveryReport(
                feature_id=feature_id,
                section_id=section_id,
                delivered_count=0,
                test_mode=test_mode,
                status="NO_OP",
                message="No scenarios found in Gherkin text.",
            )

        case_ids: List[int] = []
        for idx, title in enumerate(scenarios, start=1):
            if test_mode:
                case_ids.append(1000 + idx)
            else:
                res = add_test_case(
                    section_id=section_id,
                    title=title,
                    description=gherkin_text,
                )
                case_ids.append(res.get("id", idx))

        return DeliveryReport(
            feature_id=feature_id,
            section_id=section_id,
            delivered_count=len(case_ids),
            case_ids=case_ids,
            test_mode=test_mode,
            status="SUCCESS",
            message=f"Delivered {len(case_ids)} scenarios to TestRail section {section_id} (test_mode={test_mode}).",
        )

    def deliver_test_cases(
        self,
        feature_id: str,
        test_cases: List[TestCase],
        section_id: int,
        test_mode: bool = True,
    ) -> DeliveryReport:
        self._verify_approval(feature_id)

        if not test_cases:
            return DeliveryReport(
                feature_id=feature_id,
                section_id=section_id,
                delivered_count=0,
                test_mode=test_mode,
                status="NO_OP",
                message="No test cases provided for delivery.",
            )

        case_ids: List[int] = []
        for idx, tc in enumerate(test_cases, start=1):
            title = tc.title or f"Test Case {tc.id}"
            steps_desc = "\n".join(tc.steps) if tc.steps else ""
            if test_mode:
                case_ids.append(2000 + idx)
            else:
                res = add_test_case(
                    section_id=section_id,
                    title=title,
                    description=steps_desc,
                )
                case_ids.append(res.get("id", idx))

        return DeliveryReport(
            feature_id=feature_id,
            section_id=section_id,
            delivered_count=len(case_ids),
            case_ids=case_ids,
            test_mode=test_mode,
            status="SUCCESS",
            message=f"Delivered {len(case_ids)} test cases to TestRail section {section_id} (test_mode={test_mode}).",
        )
