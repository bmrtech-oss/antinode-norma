import pytest
import json
from pathlib import Path
import openpyxl
from antinode_norma.server.mcp_server import call_tool
from antinode_norma.core.types import TestCase


@pytest.mark.asyncio
async def test_mcp_csv_generate_and_quality_gates_e2e(tmp_path):
    csv_file = tmp_path / "orders.csv"
    csv_file.write_text(
        "ID,Summary,As a,I want to,So that,Acceptance Criteria\n"
        "TC-601,Cancel Order,shopper,cancel active order,receive refund,Order is canceled immediately\n"
    )

    out_dir = tmp_path / "features"

    # 1. Call generate_from_csv MCP tool
    gen_result = await call_tool("generate_from_csv", {
        "csv_path": str(csv_file),
        "output_dir": str(out_dir),
    })

    assert len(gen_result) == 1
    gen_data = json.loads(gen_result[0].text)
    assert gen_data["test_cases"] == 1
    assert gen_data["verdict"] == "PASS"

    feature_file = Path(gen_data["output_file"])
    assert feature_file.exists()

    # 2. Call run_quality_gates MCP tool with context test_cases to pass Q3 and Q4 traceability
    gherkin_content = feature_file.read_text(encoding="utf-8")
    test_cases = [TestCase(id="TC-601", title="Cancel Order")]

    from antinode_norma.gates.runner import GateRunner
    from antinode_norma.gates.types import GateContext

    ctx = GateContext(gherkin_text=gherkin_content, test_cases=test_cases)
    verdict = GateRunner().evaluate(ctx)

    assert verdict.hard_pass is True
    assert verdict.summary == "PASS"


@pytest.mark.asyncio
async def test_mcp_xlsx_generate_e2e(tmp_path):
    xlsx_file = tmp_path / "inventory.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["ID", "Summary", "As a", "I want to", "So that", "Acceptance Criteria"])
    ws.append(["TC-701", "Stock Check", "warehouse manager", "check stock level", "reorder items", "Displays current stock count"])
    wb.save(xlsx_file)

    out_dir = tmp_path / "features"

    result = await call_tool("generate_from_xlsx", {
        "xlsx_path": str(xlsx_file),
        "output_dir": str(out_dir),
    })

    assert len(result) == 1
    data = json.loads(result[0].text)
    assert data["test_cases"] == 1
    assert data["verdict"] == "PASS"
    assert Path(data["output_file"]).exists()
