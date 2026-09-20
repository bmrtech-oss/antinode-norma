import openpyxl
from antinode_norma.ingest_structured.csv import CSVIngester
from antinode_norma.ingest_structured.xlsx import XLSXIngester
from antinode_norma.core.agent import NormaAgent


def test_csv_ingest_with_repair_loop(tmp_path):
    csv_file = tmp_path / "test_cases.csv"
    csv_file.write_text(
        "ID,Summary,As a,I want to,So that,Acceptance Criteria\n"
        "TC-201,Order Checkout,registered customer,complete checkout,receive order,Valid payment processes order\n"
    )

    ingester = CSVIngester()
    test_cases = ingester.ingest(str(csv_file))
    assert len(test_cases) == 1
    assert test_cases[0].id == "TC-201"

    calls = 0

    def mock_llm(prompt: str) -> str:
        nonlocal calls
        calls += 1
        if calls == 1:
            # Attempt 1: Fails Q3 traceability (missing @TC-201)
            return """
Feature: Order Checkout
  Scenario: Complete checkout
    Given customer is on checkout page
    When customer submits payment
    Then order is placed
"""
        else:
            # Attempt 2: Includes @TC-201 tag
            return """
@TC-201
Feature: Order Checkout
  Scenario: Complete checkout
    Given customer is on checkout page
    When customer submits payment
    Then order is placed
"""

    agent = NormaAgent(llm_callable=mock_llm)
    gherkin_text, verdict, attempts = agent.generate_feature_with_repair(test_cases)

    assert attempts == 2
    assert verdict.hard_pass is True
    assert "@TC-201" in gherkin_text


def test_xlsx_ingest_with_single_attempt_pass(tmp_path):
    xlsx_file = tmp_path / "test_cases.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["ID", "Summary", "As a", "I want to", "So that", "Acceptance Criteria"])
    ws.append(["TC-301", "User Settings", "user", "update profile", "keep info current", "Profile is updated"])
    wb.save(xlsx_file)

    ingester = XLSXIngester()
    test_cases = ingester.ingest(str(xlsx_file))
    assert len(test_cases) == 1
    assert test_cases[0].id == "TC-301"

    def mock_llm(prompt: str) -> str:
        return """
@TC-301
Feature: User Settings
  Scenario: Update profile
    Given user is on settings page
    When user updates profile details
    Then profile is saved
"""

    agent = NormaAgent(llm_callable=mock_llm)
    gherkin_text, verdict, attempts = agent.generate_feature_with_repair(test_cases)

    assert attempts == 1
    assert verdict.hard_pass is True
    assert "@TC-301" in gherkin_text
