import openpyxl
from antinode_norma.ingest_structured.csv import CSVIngester
from antinode_norma.ingest_structured.xlsx import XLSXIngester
from antinode_norma.ingest_structured.story import story_to_case
from antinode_norma.ingest_structured.normalize import normalize
from antinode_norma.core.types import DomainModel


def test_csv_ingester(tmp_path):
    csv_file = tmp_path / "test_cases.csv"
    csv_file.write_text(
        "Case ID,Summary,As a,I want to,So that,Acceptance Criteria,Labels\n"
        "TC-101,Login Test,user,log in,access app,Valid credentials succeed; Error shown on invalid,smoke;auth\n"
    )

    ingester = CSVIngester()
    cases = ingester.ingest(csv_file)

    assert len(cases) == 1
    case = cases[0]
    assert case.id == "TC-101"
    assert case.title == "Login Test"
    assert case.role == "user"
    assert case.action == "log in"
    assert case.benefit == "access app"
    assert len(case.acceptance_criteria) == 2
    assert "Valid credentials succeed" in case.acceptance_criteria
    assert "smoke" in case.tags


def test_xlsx_ingester(tmp_path):
    xlsx_file = tmp_path / "test_cases.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "TestCases"

    ws.append(["Test ID", "Name", "Role", "Goal", "Outcome", "Criteria", "Tags"])
    ws.append(["TC-201", "Reset Password", "user", "reset password", "regain access", "Email reset link sent", "auth"])

    wb.save(xlsx_file)

    ingester = XLSXIngester(sheet_name="TestCases")
    cases = ingester.ingest(xlsx_file)

    assert len(cases) == 1
    case = cases[0]
    assert case.id == "TC-201"
    assert case.title == "Reset Password"
    assert case.action == "reset password"
    assert case.benefit == "regain access"
    assert case.acceptance_criteria == ["Email reset link sent"]


def test_story_to_case_adapter():
    story_dict = {
        "story_id": "JIRA-123",
        "role": "admin",
        "action": "manage users",
        "benefit": "control access",
        "acceptance_criteria": ["Can view list", "Can disable user"],
        "tags": ["admin"],
    }

    case = story_to_case(story_dict)
    assert case.id == "JIRA-123"
    assert case.role == "admin"
    assert len(case.acceptance_criteria) == 2


def test_unified_normalize_adapter(tmp_path):
    csv_file = tmp_path / "cases.csv"
    csv_file.write_text("ID,Summary,Action\nTC-01,Test,run\n")

    domain = DomainModel(name="test_domain")
    cases = normalize(csv_file, kind="csv", model=domain)

    assert len(cases) == 1
    assert cases[0].id == "TC-01"
    assert cases[0].metadata.get("domain_model") == "test_domain"
