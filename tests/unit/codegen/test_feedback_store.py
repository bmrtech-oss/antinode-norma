"""Unit tests for FeedbackStore."""

"""Unit tests for FeedbackStore."""

import pytest
from pathlib import Path
from antinode_norma.codegen.engine.feedback_store import FeedbackStore
import tempfile


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    import gc
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_feedback.db"
        store = FeedbackStore(db_path=db_path)
        yield store
        # Explicitly close connection before cleanup
        store.close()
        gc.collect()


def test_feedback_store_records_result(temp_db):
    """Test recording a single feedback result."""
    record = temp_db.record_result(
        step_text="click the login button",
        selector="button[aria-label='Login']",
        action_type="click",
        test_result="pass",
        mapping_source="llm",
        confidence=0.88,
    )
    assert record.test_result == "pass"
    assert record.selector == "button[aria-label='Login']"
    assert record.mapping_source == "llm"
    assert record.confidence == 0.88


def test_feedback_store_retrieves_results(temp_db):
    """Test retrieving feedback for a selector."""
    temp_db.record_result(
        step_text="click login",
        selector="button[id='login']",
        action_type="click",
        test_result="pass",
    )
    temp_db.record_result(
        step_text="click logout",
        selector="button[id='login']",
        action_type="click",
        test_result="fail",
    )

    results = temp_db.get_results_for_selector("button[id='login']")
    assert len(results) == 2
    assert results[0].test_result in ("pass", "fail")


def test_feedback_store_success_rate(temp_db):
    """Test success rate calculation."""
    # Record 3 passes and 1 fail
    for i in range(3):
        temp_db.record_result(
            step_text=f"step {i}",
            selector="button.primary",
            action_type="click",
            test_result="pass",
        )
    temp_db.record_result(
        step_text="step fail",
        selector="button.primary",
        action_type="click",
        test_result="fail",
    )

    success_rate = temp_db.get_success_rate("button.primary")
    assert success_rate == 0.75  # 3 pass / 4 total


def test_feedback_store_success_rate_no_history(temp_db):
    """Test success rate for unknown selector."""
    success_rate = temp_db.get_success_rate("unknown.selector")
    assert success_rate == 0.0


def test_feedback_store_retrieves_by_step_text(temp_db):
    """Test retrieving feedback by step text."""
    temp_db.record_result(
        step_text="click the button",
        selector="button.primary",
        action_type="click",
        test_result="pass",
    )
    temp_db.record_result(
        step_text="click the button",
        selector="button.secondary",
        action_type="click",
        test_result="fail",
    )

    results = temp_db.get_results_for_step("click the button")
    assert len(results) == 2
    assert all(r.step_text == "click the button" for r in results)


def test_feedback_store_passing_results(temp_db):
    """Test retrieving only passing results."""
    temp_db.record_result(
        step_text="step1",
        selector="selector1",
        action_type="click",
        test_result="pass",
    )
    temp_db.record_result(
        step_text="step2",
        selector="selector2",
        action_type="type",
        test_result="fail",
    )
    temp_db.record_result(
        step_text="step3",
        selector="selector3",
        action_type="click",
        test_result="pass",
    )

    results = temp_db.get_passing_results()
    assert len(results) == 2
    assert all(r.test_result == "pass" for r in results)


def test_feedback_store_passing_results_filtered_by_action(temp_db):
    """Test retrieving passing results filtered by action type."""
    temp_db.record_result(
        step_text="step1",
        selector="selector1",
        action_type="click",
        test_result="pass",
    )
    temp_db.record_result(
        step_text="step2",
        selector="selector2",
        action_type="type",
        test_result="pass",
    )
    temp_db.record_result(
        step_text="step3",
        selector="selector3",
        action_type="click",
        test_result="pass",
    )

    results = temp_db.get_passing_results(action_type="click")
    assert len(results) == 2
    assert all(r.action_type == "click" for r in results)


def test_feedback_store_execution_context(temp_db):
    """Test storing and retrieving execution context."""
    context = {
        "browser": "chromium",
        "page": "login_page",
        "error_msg": "Element not found",
    }
    record = temp_db.record_result(
        step_text="click button",
        selector="button",
        action_type="click",
        test_result="fail",
        execution_context=context,
    )

    assert record.execution_context["browser"] == "chromium"
    assert record.execution_context["page"] == "login_page"
    assert "timestamp" in record.execution_context


def test_feedback_store_duplicate_handling(temp_db):
    """Test that duplicate mappings are updated, not duplicated."""
    temp_db.record_result(
        step_text="click login",
        selector="button[aria-label='Login']",
        action_type="click",
        test_result="pass",
    )
    temp_db.record_result(
        step_text="click login",
        selector="button[aria-label='Login']",
        action_type="click",
        test_result="fail",  # Update with different result
    )

    results = temp_db.get_results_for_selector("button[aria-label='Login']")
    # Should only have 1 record (the latest)
    assert len(results) == 1
    assert results[0].test_result == "fail"


def test_feedback_store_clear_all(temp_db):
    """Test clearing all feedback."""
    temp_db.record_result(
        step_text="step1",
        selector="selector1",
        action_type="click",
        test_result="pass",
    )
    temp_db.record_result(
        step_text="step2",
        selector="selector2",
        action_type="type",
        test_result="fail",
    )

    results = temp_db.get_passing_results(limit=100)
    assert len(results) >= 1

    temp_db.clear_all()

    results = temp_db.get_passing_results(limit=100)
    assert len(results) == 0
