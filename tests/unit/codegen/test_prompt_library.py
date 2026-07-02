"""Unit tests for PromptLibrary (Phase 1.3a)."""

from antinode_norma.codegen.engine.prompt_library import (
    PromptLibrary,
    PromptTemplate,
    Domain,
)


class TestPromptLibraryCore:
    """Test PromptLibrary core functionality."""

    def test_load_builtin_templates(self):
        """Test that builtin templates load correctly."""
        lib = PromptLibrary()

        # Verify all domains loaded
        assert Domain.ECOMMERCE in lib.templates
        assert Domain.SAAS in lib.templates
        assert Domain.FINTECH in lib.templates
        assert Domain.GENERIC in lib.templates

        # Verify each has at least v1 and latest
        for domain in [Domain.ECOMMERCE, Domain.SAAS, Domain.FINTECH, Domain.GENERIC]:
            assert "v1" in lib.templates[domain]
            assert "latest" in lib.templates[domain]

    def test_get_template_default_version(self):
        """Test retrieving template with default (latest) version."""
        lib = PromptLibrary()
        template = lib.get_template(Domain.ECOMMERCE)

        assert template is not None
        assert template.domain == Domain.ECOMMERCE
        assert template.version == "v1"  # "latest" should point to v1 initially

    def test_get_template_pinned_version(self):
        """Test retrieving template with pinned version."""
        lib = PromptLibrary()
        template = lib.get_template(Domain.SAAS, version="v1")

        assert template is not None
        assert template.domain == Domain.SAAS
        assert template.version == "v1"

    def test_get_template_invalid_domain(self):
        """Test retrieving template for invalid domain."""
        lib = PromptLibrary()
        template = lib.get_template(Domain.ECOMMERCE, version="nonexistent")

        assert template is None

    def test_add_new_template(self):
        """Test adding new template version."""
        lib = PromptLibrary()

        new_template = PromptTemplate(
            domain=Domain.ECOMMERCE,
            version="v2",
            system_prompt="New ecommerce system prompt",
            few_shot_examples=[
                "Example 1",
                "Example 2",
                "Example 3",
                "Example 4",
                "Example 5",
            ],
            chain_of_thought="New chain of thought",
        )

        result = lib.add_template(new_template)
        assert result is True

        # Verify it was added
        retrieved = lib.get_template(Domain.ECOMMERCE, version="v2")
        assert retrieved is not None
        assert retrieved.version == "v2"

    def test_list_versions(self):
        """Test listing versions for a domain."""
        lib = PromptLibrary()
        versions = lib.list_versions(Domain.ECOMMERCE)

        assert "v1" in versions
        assert "latest" in versions

    def test_get_system_prompt_with_examples(self):
        """Test getting formatted system prompt with examples."""
        lib = PromptLibrary()
        prompt = lib.get_system_prompt(Domain.ECOMMERCE)

        assert prompt is not None
        assert "ecommerce" in prompt.lower()
        assert "Examples:" in prompt
        assert "add" in prompt.lower() or "cart" in prompt.lower()  # Should contain example
        assert "Chain of Thought:" in prompt

    def test_get_system_prompt_invalid_domain(self):
        """Test getting system prompt for invalid domain."""
        lib = PromptLibrary()
        prompt = lib.get_system_prompt(Domain.ECOMMERCE, version="nonexistent")

        assert prompt is None

    def test_template_validation(self):
        """Test PromptTemplate validation."""
        # Valid template
        valid = PromptTemplate(
            domain=Domain.SAAS,
            version="v1",
            system_prompt="System",
            few_shot_examples=["Ex1", "Ex2", "Ex3", "Ex4", "Ex5"],
            chain_of_thought="CoT",
        )
        assert valid.validate() is True

        # Invalid: not enough examples
        invalid_examples = PromptTemplate(
            domain=Domain.SAAS,
            version="v1",
            system_prompt="System",
            few_shot_examples=["Ex1", "Ex2"],  # Only 2, need 5+
            chain_of_thought="CoT",
        )
        assert invalid_examples.validate() is False

        # Invalid: missing system prompt
        invalid_system = PromptTemplate(
            domain=Domain.SAAS,
            version="v1",
            system_prompt="",
            few_shot_examples=["Ex1", "Ex2", "Ex3", "Ex4", "Ex5"],
            chain_of_thought="CoT",
        )
        assert invalid_system.validate() is False


class TestDomainTemplates:
    """Test domain-specific template content."""

    def test_ecommerce_template_has_checkout_keywords(self):
        """Test ecommerce template contains checkout-related keywords."""
        lib = PromptLibrary()
        template = lib.get_template(Domain.ECOMMERCE)

        content = template.system_prompt + " ".join(template.few_shot_examples)
        assert "checkout" in content.lower() or "cart" in content.lower()

    def test_saas_template_has_login_keywords(self):
        """Test SaaS template contains login-related keywords."""
        lib = PromptLibrary()
        template = lib.get_template(Domain.SAAS)

        content = template.system_prompt + " ".join(template.few_shot_examples)
        assert "login" in content.lower() or "dashboard" in content.lower()

    def test_fintech_template_has_transfer_keywords(self):
        """Test fintech template contains transfer/balance keywords."""
        lib = PromptLibrary()
        template = lib.get_template(Domain.FINTECH)

        content = template.system_prompt + " ".join(template.few_shot_examples)
        assert (
            "balance" in content.lower()
            or "transfer" in content.lower()
            or "account" in content.lower()
        )

    def test_all_templates_have_minimum_examples(self):
        """Test all templates have at least 5 examples."""
        lib = PromptLibrary()

        for domain in [Domain.ECOMMERCE, Domain.SAAS, Domain.FINTECH, Domain.GENERIC]:
            template = lib.get_template(domain)
            assert len(template.few_shot_examples) >= 5


class TestPromptFormatting:
    """Test prompt formatting and composition."""

    def test_system_prompt_includes_examples(self):
        """Test formatted prompt includes few-shot examples."""
        lib = PromptLibrary()
        prompt = lib.get_system_prompt(Domain.ECOMMERCE)

        # Should have examples section
        lines = prompt.split("\n")
        has_examples_section = any("Examples:" in line for line in lines)
        assert has_examples_section is True

    def test_system_prompt_includes_chain_of_thought(self):
        """Test formatted prompt includes chain of thought."""
        lib = PromptLibrary()
        prompt = lib.get_system_prompt(Domain.SAAS)

        assert "Chain of Thought:" in prompt

    def test_system_prompt_all_domains_have_priority_order(self):
        """Test all prompts mention selector priority."""
        lib = PromptLibrary()

        for domain in [Domain.ECOMMERCE, Domain.SAAS, Domain.FINTECH, Domain.GENERIC]:
            prompt = lib.get_system_prompt(domain)
            assert "data-testid" in prompt or "testid" in prompt.lower()
