import json

from antinode_aegis.trace import TraceRenderer


def test_aegis_trace_renderer_marks_coverage():
    matrix = TraceRenderer.build_matrix(
        feature_title="Account",
        requirements=[
            {"id": "REQ-801", "title": "View balance"},
            {"id": "REQ-802", "title": "Export balance"},
        ],
        scenarios=[
            {
                "title": "View account balance",
                "requirement_ids": ["REQ-801"],
                "tags": ["@REQ-801"],
            }
        ],
        metadata={"profile": "aegis-foundation"},
    )

    assert [item.status for item in matrix.items] == ["COVERED", "UNCOVERED"]
    assert matrix.items[0].scenario_title == "View account balance"
    assert matrix.metadata["profile"] == "aegis-foundation"


def test_aegis_trace_renderer_outputs_markdown_and_json():
    matrix = TraceRenderer.build_matrix(
        feature_title="Login",
        requirements=[{"id": "REQ-803", "title": "Login"}],
        scenarios=[],
    )

    markdown = TraceRenderer.render_markdown(matrix)
    document = json.loads(TraceRenderer.render_json(matrix))

    assert "Aegis Traceability — Login" in markdown
    assert "**UNCOVERED**" in markdown
    assert document["items"][0]["requirement_id"] == "REQ-803"
