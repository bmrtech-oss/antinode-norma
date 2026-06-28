from pathlib import Path

import pytest

from antinode_norma.server.tools.codegen_tools import handle_generate_and_autocorrect


class DummyFailure:
    def __init__(self, step_text, selector, error_message):
        self.step_text = step_text
        self.selector = selector
        self.error_message = error_message


@pytest.mark.asyncio
async def test_generate_and_autocorrect_non_destructive_and_approve(monkeypatch, tmp_path):
    # Prepare a fake feature file
    feature = tmp_path / "sample.feature"
    feature.write_text("Feature: Sample\n\n  Scenario: Test\n    Given I do something")

    # Stub Orchestrator.generate to create an output dir and a fake test file
    class DummyOrch:
        def generate(self, feature_path, output_dir, framework=None):
            out = Path(output_dir)
            out.mkdir(parents=True, exist_ok=True)
            (out / "dummy.spec.ts").write_text("// generated test")

    monkeypatch.setattr("antinode_norma.server.tools.codegen_tools.Orchestrator", lambda: DummyOrch())

    # Stub subprocess.run for playwright to return empty stdout
    class Proc:
        def __init__(self):
            self.stdout = "[]"

    monkeypatch.setattr("antinode_norma.server.tools.codegen_tools.subprocess.run", lambda *a, **k: Proc())

    # Stub failure_analyzer to return a fake failure on first call, then none
    failures = [DummyFailure("Given I do something", "#btn", "Error: not found")]

    def store_once(path):
        # consume the failure once, then return [] subsequently
        if not hasattr(store_once, "called"):
            store_once.called = True
            return failures
        return []

    monkeypatch.setattr("antinode_norma.server.tools.codegen_tools.failure_analyzer.store_playwright_failures", store_once)

    # Stub LLM to return fixed content
    def fake_llm(prompt):
        return "Feature: Sample\n\n  Scenario: Test\n    Given I do something else"

    monkeypatch.setattr("antinode_norma.server.tools.codegen_tools.create_llm_callable", lambda cfg: fake_llm)

    # Ensure git isn't required for this test
    monkeypatch.setattr("antinode_norma.server.tools.codegen_tools.shutil.which", lambda name: "playwright")

    # Call handler with non_destructive and approve True to skip interactive prompt
    args = {"feature_path": str(feature), "non_destructive": True, "approve": True, "run_tests": True, "max_iterations": 2}
    result = await handle_generate_and_autocorrect(args)

    assert isinstance(result, list)
    text = result[0]["text"]
    assert "Applied LLM-suggested Gherkin fixes" in text or "Tests passed" in text

    # Check that the autcorrected file exists
    fixed_path = feature.with_name(feature.stem + ".autocorrected.feature")
    assert fixed_path.exists()
