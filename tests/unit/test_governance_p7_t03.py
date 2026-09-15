from antinode_norma.governance.traceability import TraceabilityRenderer
from antinode_norma.core.types import TestCase


def test_traceability_build_from_gherkin():
    gherkin = """
    Feature: Account Transfers

      @TC-101
      Scenario: User transfers money
        Given user logs in
        When transfer is submitted
        Then transfer succeeds
    """
    matrix = TraceabilityRenderer.build_matrix(gherkin_text=gherkin)
    assert matrix.feature_title == "Account Transfers"
    assert len(matrix.items) == 1
    assert matrix.items[0].requirement_id == "@TC-101"
    assert matrix.items[0].scenario_title == "User transfers money"


def test_traceability_render_markdown_and_json():
    gherkin = """
    Feature: Payments

      @REQ-1
      Scenario: Process payment
        Given active card
        When payment processed
        Then receipt generated
    """
    matrix = TraceabilityRenderer.build_matrix(gherkin_text=gherkin)
    md_output = TraceabilityRenderer.render_markdown(matrix)
    json_output = TraceabilityRenderer.render_json(matrix)

    assert "# Traceability Matrix — Payments" in md_output
    assert "`@REQ-1`" in md_output
    assert '"feature_title": "Payments"' in json_output


def test_traceability_test_cases_input():
    tc1 = TestCase(id="TC-201", title="Validate Login", steps=["Given user at login page"])
    matrix = TraceabilityRenderer.build_matrix(test_cases=[tc1])

    assert len(matrix.items) == 1
    assert matrix.items[0].requirement_id == "TC-201"
    assert matrix.items[0].requirement_title == "Validate Login"
