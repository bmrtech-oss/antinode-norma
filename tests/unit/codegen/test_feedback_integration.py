"""Integration tests for Phase 2: Feedback recording and learning."""

import pytest
from pathlib import Path
from antinode_norma.codegen.engine.llm_step_mapper import LLMStepMapper
from antinode_norma.codegen.engine.feedback_store import FeedbackStore
from antinode_norma.codegen.models.test_model import ActionType
import tempfile


@pytest.fixture
def temp_feedback_store():
    """Create a temporary feedback store for testing."""
    import gc
    with tempfile.TemporaryDirectory() as tmpdir:
        store = FeedbackStore(db_path=Path(tmpdir) / "integration_test.db")
        yield store
        # Explicitly close connection before cleanup
        store.close()
        gc.collect()


class TestFeedbackIntegration:
    """Test end-to-end feedback recording and learning."""

    def test_mapper_records_mapping_result(self, temp_feedback_store):
        """Test that mapper can record mapping results to feedback store."""
        mapper = LLMStepMapper(feedback_store=temp_feedback_store)
        
        # Record a successful mapping
        mapper.record_result(
            step_text="click the login button",
            selector="button[aria-label='Login']",
            action_type=ActionType.CLICK,
            test_result="pass",
            mapping_source="llm",
            confidence=0.88,
        )
        
        # Verify it was stored
        success_rate = mapper.get_selector_success_rate("button[aria-label='Login']")
        assert success_rate == 1.0  # 1 pass / 1 total

    def test_success_rate_increases_with_passes(self, temp_feedback_store):
        """Test that success rate increases as more passes are recorded."""
        mapper = LLMStepMapper(feedback_store=temp_feedback_store)
        selector = "button.primary"
        
        # Record 3 passes and 1 fail
        for _ in range(3):
            mapper.record_result(
                step_text="click button",
                selector=selector,
                action_type=ActionType.CLICK,
                test_result="pass",
            )
        mapper.record_result(
            step_text="click button",
            selector=selector,
            action_type=ActionType.CLICK,
            test_result="fail",
        )
        
        success_rate = mapper.get_selector_success_rate(selector)
        assert success_rate == 0.75  # 3 pass / 4 total

    def test_mapper_can_retrieve_proven_mappings(self, temp_feedback_store):
        """Test that mapper can retrieve previously successful mappings."""
        mapper = LLMStepMapper(
            feedback_store=temp_feedback_store,
            similarity_threshold=0.5,  # Lower threshold for testing
        )
        
        # Record a successful mapping
        mapper.record_result(
            step_text="click the login button",
            selector="button[aria-label='Login']",
            action_type=ActionType.CLICK,
            test_result="pass",
            mapping_source="llm",
            confidence=0.88,
        )
        
        # Record another successful mapping for a similar step
        mapper.record_result(
            step_text="click the login btn",
            selector="button[aria-label='Login']",
            action_type=ActionType.CLICK,
            test_result="pass",
            mapping_source="llm",
            confidence=0.88,
        )
        
        # Get passing results - should retrieve both
        passing = temp_feedback_store.get_passing_results(limit=100)
        assert len(passing) == 2
        assert all(r.test_result == "pass" for r in passing)

    def test_selector_alternatives_in_mapping_result(self, temp_feedback_store):
        """Test that LLM mappings include selector alternatives."""
        mapper = LLMStepMapper(feedback_store=temp_feedback_store)
        
        # Create a mapping result manually (simulating LLM output)
        from antinode_norma.codegen.engine.llm_step_mapper import MappingResult, SelectorGenerator
        
        mapping = MappingResult(
            action_type=ActionType.CLICK,
            selector="button[data-testid='login-btn'][aria-label='Login']",
            value=None,
            options={},
            confidence=0.88,
            source="llm",
            reason="LLM generated selector",
            step_text="click the login button",
        )
        
        # Add selector alternatives
        candidates = SelectorGenerator.generate_alternatives(mapping.selector)
        mapping.selector_candidates = candidates
        
        # Verify alternatives were generated
        assert mapping.selector_candidates is not None
        assert len(mapping.selector_candidates) >= 2
        assert mapping.selector_candidates[0].value == mapping.selector  # Original first
        
        # Verify alternatives have priority ordering
        priorities = [c.priority for c in mapping.selector_candidates]
        assert priorities == sorted(priorities)

    def test_feedback_with_execution_context(self, temp_feedback_store):
        """Test recording feedback with execution context."""
        mapper = LLMStepMapper(feedback_store=temp_feedback_store)
        
        execution_context = {
            "browser": "chromium",
            "page": "login_page",
            "error_msg": None,
        }
        
        mapper.record_result(
            step_text="click login",
            selector="button#login",
            action_type=ActionType.CLICK,
            test_result="pass",
            execution_context=execution_context,
        )
        
        # Verify context was stored
        results = temp_feedback_store.get_results_for_selector("button#login")
        assert len(results) == 1
        assert results[0].execution_context["browser"] == "chromium"
        assert results[0].execution_context["page"] == "login_page"

    def test_feedback_learning_from_failures(self, temp_feedback_store):
        """Test that failure feedback is recorded for learning."""
        mapper = LLMStepMapper(feedback_store=temp_feedback_store)
        
        # Record some failed attempts
        selector = "input.email-field"
        for i in range(3):
            mapper.record_result(
                step_text=f"enter email {i}",
                selector=selector,
                action_type=ActionType.FILL,
                test_result="fail",
                execution_context={"error_msg": "Element not found"},
            )
        
        # Record a successful alternative
        alt_selector = "input[data-testid='email-input']"
        mapper.record_result(
            step_text="enter email",
            selector=alt_selector,
            action_type=ActionType.FILL,
            test_result="pass",
        )
        
        # Original selector should have 0% success rate
        assert mapper.get_selector_success_rate(selector) == 0.0
        
        # Alternative should have 100% success rate
        assert mapper.get_selector_success_rate(alt_selector) == 1.0

    def test_multiple_mappers_share_feedback_store(self, temp_feedback_store):
        """Test that multiple mapper instances can share the same feedback store."""
        mapper1 = LLMStepMapper(feedback_store=temp_feedback_store)
        mapper2 = LLMStepMapper(feedback_store=temp_feedback_store)
        
        # Mapper1 records a result
        mapper1.record_result(
            step_text="click button",
            selector="button.primary",
            action_type=ActionType.CLICK,
            test_result="pass",
        )
        
        # Mapper2 should be able to retrieve it
        success_rate = mapper2.get_selector_success_rate("button.primary")
        assert success_rate == 1.0
