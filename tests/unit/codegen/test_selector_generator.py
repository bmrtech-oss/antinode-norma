"""Unit tests for SelectorGenerator (Phase 1.2)."""

from antinode_norma.codegen.engine.llm_step_mapper import SelectorGenerator, SelectorCandidate


class TestSelectorGenerator:
    """Test selector alternative generation."""

    def test_generate_alternatives_from_data_testid(self):
        """Test generating alternatives from a data-testid selector."""
        selector = "[data-testid='login-button']"
        candidates = SelectorGenerator.generate_alternatives(selector)
        
        assert len(candidates) >= 2
        assert candidates[0].value == selector  # Original first
        assert any("data-testid" in c.value for c in candidates)

    def test_generate_alternatives_from_aria_label(self):
        """Test generating alternatives from an aria-label selector."""
        selector = "button[aria-label='Submit']"
        candidates = SelectorGenerator.generate_alternatives(selector)
        
        assert len(candidates) >= 2
        # Should have original and aria-label variant
        assert any(c.reason == "aria-label attribute (semantic)" for c in candidates)

    def test_generate_alternatives_sorted_by_priority(self):
        """Test that alternatives are sorted by priority."""
        selector = "[data-testid='btn'][aria-label='Submit']"
        candidates = SelectorGenerator.generate_alternatives(selector)
        
        # Should be sorted by priority (lower priority value = higher priority)
        priorities = [c.priority for c in candidates]
        assert priorities == sorted(priorities)

    def test_generate_alternatives_with_no_selector(self):
        """Test generating alternatives for None or empty selector."""
        assert SelectorGenerator.generate_alternatives(None) == []
        assert SelectorGenerator.generate_alternatives("") == []

    def test_readability_score_prefers_short_selectors(self):
        """Test that readability scoring prefers shorter selectors."""
        short = "[id='btn']"
        long = "/html/body/div[1]/div[2]/section/article/div/p/button[contains(text(), 'Submit')]"
        
        short_score = SelectorGenerator._get_readability_score(short)
        long_score = SelectorGenerator._get_readability_score(long)
        
        assert short_score > long_score

    def test_readability_score_prefers_data_testid(self):
        """Test that readability scoring favors data-testid."""
        with_testid = "[data-testid='btn']"
        without_testid = "[class='btn-primary']"
        
        with_score = SelectorGenerator._get_readability_score(with_testid)
        without_score = SelectorGenerator._get_readability_score(without_testid)
        
        # data-testid should have higher readability
        assert with_score > without_score

    def test_readability_score_penalizes_xpath(self):
        """Test that readability scoring penalizes XPath selectors."""
        css = "button.primary"
        xpath = "//button[@class='primary']"
        
        css_score = SelectorGenerator._get_readability_score(css)
        xpath_score = SelectorGenerator._get_readability_score(xpath)
        
        assert css_score > xpath_score

    def test_extract_testid(self):
        """Test extracting data-testid from selector."""
        selector = "[data-testid='login-btn']"
        testid = SelectorGenerator._extract_testid(selector)
        assert testid == "login-btn"

    def test_extract_aria_label(self):
        """Test extracting aria-label from selector."""
        selector = "button[aria-label='Click me']"
        label = SelectorGenerator._extract_aria_label(selector)
        assert label == "Click me"

    def test_extract_role(self):
        """Test extracting role from selector."""
        selector = "[role='button'][aria-label='Submit']"
        role = SelectorGenerator._extract_role(selector)
        assert role == "button"

    def test_selector_candidate_dataclass(self):
        """Test SelectorCandidate creation and attributes."""
        candidate = SelectorCandidate(
            value="[data-testid='btn']",
            priority=1,
            readability=0.95,
            reason="data-testid attribute",
        )
        
        assert candidate.value == "[data-testid='btn']"
        assert candidate.priority == 1
        assert candidate.readability == 0.95
        assert candidate.reason == "data-testid attribute"

    def test_generate_alternatives_original_is_primary(self):
        """Test that the original selector is always first with priority 0."""
        selector = "button.primary"
        candidates = SelectorGenerator.generate_alternatives(selector)
        
        assert len(candidates) > 0
        assert candidates[0].value == selector
        assert candidates[0].priority == 0
        assert candidates[0].reason == "Original selector from mapping"
