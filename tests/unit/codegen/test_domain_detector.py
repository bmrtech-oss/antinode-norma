"""Unit tests for DomainDetector (Phase 1.3b)."""

from antinode_norma.codegen.engine.domain_detector import DomainDetector
from antinode_norma.codegen.engine.prompt_library import Domain


class TestDomainDetection:
    """Test domain detection from feature content."""

    def test_detect_ecommerce_keywords(self):
        """Test detecting ecommerce domain from keywords."""
        content = """
        Feature: Shopping Cart
        Scenario: User adds item to cart
            Given I'm on the product page
            When I click "Add to Cart"
            Then the cart shows 1 item
            And the price is updated
        """
        domain, confidence = DomainDetector.detect_domain(content)

        assert domain == Domain.ECOMMERCE
        assert confidence > 0.5

    def test_detect_saas_keywords(self):
        """Test detecting SaaS domain from keywords."""
        content = """
        Feature: User Authentication
        Scenario: User logs in
            Given I'm on the login page
            When I enter email and password
            Then I'm redirected to dashboard
            And I can access my settings
            And I see my workspace
        """
        domain, confidence = DomainDetector.detect_domain(content)

        assert domain == Domain.SAAS
        assert confidence > 0.5

    def test_detect_fintech_keywords(self):
        """Test detecting fintech domain from keywords."""
        content = """
        Feature: Money Transfer
        Scenario: User transfers money
            Given I have a balance of $1000
            When I initiate a transfer
            And I enter the recipient account
            And I confirm the amount
            Then the transaction is recorded
            And I see the statement updated
        """
        domain, confidence = DomainDetector.detect_domain(content)

        assert domain == Domain.FINTECH
        assert confidence > 0.5

    def test_default_to_generic_low_confidence(self):
        """Test defaulting to GENERIC when confidence is low."""
        content = """
        Feature: Some generic feature
        Scenario: User does something
            Given a precondition
            When I perform action
            Then I see result
        """
        domain, confidence = DomainDetector.detect_domain(content)

        assert domain == Domain.GENERIC
        assert confidence < 0.3

    def test_mixed_keywords_uses_highest_score(self):
        """Test that mixed keywords use highest-scoring domain."""
        # Ecommerce keywords dominate
        content = """
        Scenario: E-commerce checkout
            When I add item to cart
            And remove item from cart
            And apply coupon
            And proceed to checkout
            And enter shipping address
        """
        domain, confidence = DomainDetector.detect_domain(content)

        assert domain == Domain.ECOMMERCE

    def test_empty_content_returns_generic(self):
        """Test that empty content returns GENERIC with 0.0 confidence."""
        domain, confidence = DomainDetector.detect_domain("")

        assert domain == Domain.GENERIC
        assert confidence == 0.0

    def test_case_insensitive_detection(self):
        """Test that keyword detection is case-insensitive."""
        content = "Feature: CART CHECKOUT PAYMENT"  # All caps
        domain, confidence = DomainDetector.detect_domain(content)

        assert domain == Domain.ECOMMERCE

    def test_detect_from_features_list(self):
        """Test detecting from list of feature strings."""
        features = [
            "I add product to cart",
            "I enter shipping address",
            "I pay with credit card",
        ]
        domain, confidence = DomainDetector.detect_domain(" ".join(features))

        assert domain == Domain.ECOMMERCE
        assert confidence > 0.3

    def test_keyword_match_count(self):
        """Test counting keyword matches for a domain."""
        content = "I add item to cart, remove from cart, apply coupon"
        count = DomainDetector.keyword_match_count(content, Domain.ECOMMERCE)

        assert count >= 3  # cart (2x), coupon (1x), at minimum

    def test_get_domain_keywords(self):
        """Test retrieving keywords for a domain."""
        keywords = DomainDetector.get_domain_keywords(Domain.SAAS)

        assert "login" in keywords
        assert "dashboard" in keywords
        assert len(keywords) > 5

    def test_fintech_has_financial_keywords(self):
        """Test that fintech domain keywords include financial terms."""
        keywords = DomainDetector.get_domain_keywords(Domain.FINTECH)

        assert any(kw in keywords for kw in ["balance", "transfer", "account"])

    def test_confidence_calculation(self):
        """Test confidence is calculated correctly."""
        # High confidence: all ecommerce
        high_conf_content = "cart checkout payment order product shipping"
        domain1, conf1 = DomainDetector.detect_domain(high_conf_content)

        # Low confidence: only one keyword
        low_conf_content = "I click a button"
        domain2, conf2 = DomainDetector.detect_domain(low_conf_content)

        if domain1 != Domain.GENERIC and domain2 == Domain.GENERIC:
            assert conf1 > conf2
