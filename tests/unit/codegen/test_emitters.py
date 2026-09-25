from pathlib import Path

from antinode_norma.codegen.emitters.page_object_emitter import PageObjectEmitter
from antinode_norma.codegen.emitters.scenario_outline_emitter import ScenarioOutlineEmitter
from antinode_norma.codegen.emitters.step_def_emitter import StepDefEmitter
from antinode_norma.codegen.models.test_model import ActionType, TestCase, TestStep, TestSuite


def _make_suite() -> TestSuite:
    return TestSuite(
        name="login_flow",
        cases=[
            TestCase(
                name="user logs in",
                steps=[
                    TestStep(
                        action=ActionType.NAVIGATE,
                        value="https://example.com/login",
                        description="Visit login page",
                    ),
                    TestStep(
                        action=ActionType.FILL,
                        target="[data-testid='email']",
                        value="user@example.com",
                        description="Enter email",
                    ),
                    TestStep(
                        action=ActionType.CLICK,
                        target="button[type='submit']",
                        description="Submit form",
                    ),
                ],
            )
        ],
    )


def test_page_object_emitter_generates_page_object_file(tmp_path: Path):
    emitter = PageObjectEmitter()
    suite = _make_suite()

    emitter.emit(suite, tmp_path / "generated")

    page_files = list((tmp_path / "generated").glob("*.page.ts"))
    assert len(page_files) == 1
    content = page_files[0].read_text(encoding="utf-8")
    assert "class" in content
    assert "page.locator" in content


def test_step_def_emitter_generates_step_file(tmp_path: Path):
    emitter = StepDefEmitter()
    suite = _make_suite()

    emitter.emit(suite, tmp_path / "generated")

    steps_file = tmp_path / "generated" / "common_steps.ts"
    assert steps_file.exists()
    content = steps_file.read_text(encoding="utf-8")
    assert "navigateTo" in content
    assert "fillField" in content
    assert "clickElement" in content


def test_scenario_outline_emitter_generates_outline_file(tmp_path: Path):
    emitter = ScenarioOutlineEmitter()
    suite = _make_suite()

    emitter.emit(suite, tmp_path / "generated")

    outline_file = tmp_path / "generated" / "login_flow_outline.spec.ts"
    assert outline_file.exists()
    content = outline_file.read_text(encoding="utf-8")
    assert "describe" in content
    assert "for" in content or "test.each" in content
