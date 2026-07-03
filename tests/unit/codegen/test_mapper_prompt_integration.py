"""Integration tests for Phase 1.3c: LLMStepMapper + PromptLibrary."""

import pytest
from antinode_norma.codegen.config import CodegenConfig
from antinode_norma.codegen.engine.llm_step_mapper import LLMStepMapper
from antinode_norma.codegen.engine.prompt_library import Domain
from antinode_norma.codegen.engine.feedback_store import FeedbackStore


class TestLLMStepMapperIntegration:
    """Test LLMStepMapper integration with PromptLibrary."""

    @pytest.fixture
    def temp_feedback_store(self, tmp_path):
        """Create temporary feedback store for testing."""
        db_path = tmp_path / "test_feedback.db"
        store = FeedbackStore(db_path=db_path)
        yield store
        store.close()

    def test_mapper_initializes_with_domain(self, temp_feedback_store):
        """Test that mapper can be initialized with a domain."""
        mapper = LLMStepMapper(
            feedback_store=temp_feedback_store,
            domain=Domain.ECOMMERCE,
            prompt_version="v1",
        )

        assert mapper.domain == Domain.ECOMMERCE
        assert mapper.prompt_version == "v1"

    def test_mapper_defaults_to_generic_domain(self, temp_feedback_store):
        """Test that mapper defaults to GENERIC domain."""
        mapper = LLMStepMapper(feedback_store=temp_feedback_store)

        assert mapper.domain == Domain.GENERIC

    def test_set_domain_updates_domain(self, temp_feedback_store):
        """Test that set_domain updates the mapper's domain."""
        mapper = LLMStepMapper(feedback_store=temp_feedback_store)
        mapper.set_domain(Domain.SAAS)

        assert mapper.domain == Domain.SAAS

    def test_auto_detect_domain_from_feature(self, temp_feedback_store):
        """Test auto-detecting domain from feature content."""
        mapper = LLMStepMapper(feedback_store=temp_feedback_store)
        
        ecommerce_content = """
        Feature: Shopping
        Scenario: User adds to cart
            Given I'm on the product page
            When I click add to cart
            Then the item is in my cart
        """
        
        detected_domain = mapper.auto_detect_domain(ecommerce_content)
        assert detected_domain == Domain.ECOMMERCE
        assert mapper.domain == Domain.ECOMMERCE

    def test_build_system_prompt_returns_domain_specific(self, temp_feedback_store):
        """Test that _build_system_prompt returns domain-specific content."""
        mapper = LLMStepMapper(
            feedback_store=temp_feedback_store,
            domain=Domain.ECOMMERCE,
        )
        
        prompt = mapper._build_system_prompt()
        
        assert prompt is not None
        assert "ecommerce" in prompt.lower() or "checkout" in prompt.lower() or "cart" in prompt.lower()
        assert "Examples:" in prompt
        assert "Chain of Thought:" in prompt

    def test_build_system_prompt_saas_domain(self, temp_feedback_store):
        """Test SaaS domain prompt generation."""
        mapper = LLMStepMapper(
            feedback_store=temp_feedback_store,
            domain=Domain.SAAS,
        )
        
        prompt = mapper._build_system_prompt()
        
        assert "saas" in prompt.lower() or "login" in prompt.lower() or "dashboard" in prompt.lower()

    def test_build_system_prompt_fintech_domain(self, temp_feedback_store):
        """Test fintech domain prompt generation."""
        mapper = LLMStepMapper(
            feedback_store=temp_feedback_store,
            domain=Domain.FINTECH,
        )
        
        prompt = mapper._build_system_prompt()
        
        assert (
            "fintech" in prompt.lower() or
            "balance" in prompt.lower() or
            "transfer" in prompt.lower() or
            "account" in prompt.lower()
        )

    def test_prompt_version_pinning(self, temp_feedback_store):
        """Test that prompt version can be pinned."""
        mapper = LLMStepMapper(
            feedback_store=temp_feedback_store,
            domain=Domain.ECOMMERCE,
            prompt_version="v1",
        )
        
        assert mapper.prompt_version == "v1"
        
        # Should retrieve v1 template
        template = mapper.prompt_library.get_template(Domain.ECOMMERCE, "v1")
        assert template is not None
        assert template.version == "v1"

    def test_mapper_uses_domain_prompt_in_build(self, temp_feedback_store):
        """Test that mapper's domain affects prompt building."""
        ecommerce_mapper = LLMStepMapper(
            feedback_store=temp_feedback_store,
            domain=Domain.ECOMMERCE,
        )
        
        saas_mapper = LLMStepMapper(
            feedback_store=temp_feedback_store,
            domain=Domain.SAAS,
        )
        
        ecommerce_prompt = ecommerce_mapper._build_system_prompt()
        saas_prompt = saas_mapper._build_system_prompt()
        
        # Prompts should be different
        assert ecommerce_prompt != saas_prompt

    def test_prompt_library_initialized(self, temp_feedback_store):
        """Test that mapper initializes PromptLibrary."""
        mapper = LLMStepMapper(feedback_store=temp_feedback_store)
        
        assert mapper.prompt_library is not None
        assert len(mapper.prompt_library.list_versions(Domain.ECOMMERCE)) > 0

    def test_domain_detection_integration(self, temp_feedback_store):
        """Test end-to-end domain detection and prompt building."""
        mapper = LLMStepMapper(feedback_store=temp_feedback_store)
        
        # Start with generic
        assert mapper.domain == Domain.GENERIC
        
        # Auto-detect ecommerce
        ecommerce_features = "I add product to cart and checkout with payment"
        mapper.auto_detect_domain(ecommerce_features)
        assert mapper.domain == Domain.ECOMMERCE
        
        # Check prompt is now ecommerce-specific
        prompt = mapper._build_system_prompt()
        assert "checkout" in prompt.lower() or "cart" in prompt.lower() or "payment" in prompt.lower()

    def test_gherkin_parser_uses_codegen_config_for_mapper(self, tmp_path, monkeypatch):
        """Test that GherkinParser loads domain and prompt version from config."""
        from antinode_norma.codegen.parsers.gherkin_parser import GherkinParser

        config = CodegenConfig(domain="saas", prompt_version="v1")
        monkeypatch.setattr(
            "antinode_norma.codegen.parsers.gherkin_parser.get_config",
            lambda: config,
        )

        parser = GherkinParser(use_richer_mapper=True)
        assert parser.mapper is not None
        assert parser.mapper.domain == Domain.SAAS
        assert parser.mapper.prompt_version == "v1"
