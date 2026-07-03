"""Domain-specific prompt templates for step mapping."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum
from datetime import datetime


class Domain(Enum):
    """Supported domains for prompt templates."""

    ECOMMERCE = "ecommerce"
    SAAS = "saas"
    FINTECH = "fintech"
    GENERIC = "generic"


@dataclass
class PromptTemplate:
    """Single domain prompt with examples and chain-of-thought."""

    domain: Domain
    version: str  # e.g., "v1", "v2"
    system_prompt: str  # Domain context and expertise
    few_shot_examples: List[str]  # List of example step→selector mappings
    chain_of_thought: str  # Structured reasoning instructions
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def validate(self) -> bool:
        """Check that template has required fields and examples."""
        if not self.system_prompt or not self.few_shot_examples or not self.chain_of_thought:
            return False
        if len(self.few_shot_examples) < 5:
            return False
        return True


class PromptLibrary:
    """Manages domain-specific prompt templates with versioning."""

    def __init__(self):
        """Initialize library with built-in templates."""
        self.templates: Dict[Domain, Dict[str, PromptTemplate]] = {
            domain: {} for domain in Domain
        }
        self._load_builtin_templates()

    def _load_builtin_templates(self) -> None:
        """Load built-in templates for each domain."""
        # Ecommerce templates
        ecommerce_v1 = PromptTemplate(
            domain=Domain.ECOMMERCE,
            version="v1",
            system_prompt="""You are an expert Playwright test step mapper for ecommerce platforms.
You understand checkout flows, cart operations, product pages, and payment flows.
Map natural language test steps to CSS selectors, XPath, or accessibility attributes.
Priority: data-testid > aria-label > role > semantic selectors > CSS classes > XPath.""",
            few_shot_examples=[
                "Step: 'I add the product to cart' → Selector: 'button[data-testid=\"add-to-cart\"]'",
                "Step: 'I click the checkout button' → Selector: 'a[href=\"/checkout\"]' or 'button:has-text(\"Proceed to Checkout\")'",
                "Step: 'I enter shipping address' → Selector: 'input[data-testid=\"shipping-address\"]'",
                "Step: 'I select payment method' → Selector: 'select[name=\"payment_method\"]' or 'input[aria-label=\"Credit Card\"]'",
                "Step: 'I view order summary' → Selector: 'div[data-testid=\"order-summary\"]' or 'section:has-text(\"Order Summary\")'",
                "Step: 'I apply coupon code' → Selector: 'input[placeholder=\"Enter coupon code\"]' or 'input[aria-label*=\"coupon\"]'",
                "Step: 'I remove item from cart' → Selector: 'button[aria-label*=\"Remove\"]' or 'a[data-testid=\"remove-item\"]'",
            ],
            chain_of_thought="""1. Identify element type (button, input, link, etc.)
2. Check for data-testid attribute (highest priority)
3. Look for aria-label or role attributes (accessibility)
4. Try semantic selectors (button:has-text, a[href])
5. Fall back to CSS classes if semantic fails
6. Use XPath only as last resort""",
        )
        self.templates[Domain.ECOMMERCE]["v1"] = ecommerce_v1
        self.templates[Domain.ECOMMERCE]["latest"] = ecommerce_v1

        # SaaS templates
        saas_v1 = PromptTemplate(
            domain=Domain.SAAS,
            version="v1",
            system_prompt="""You are an expert Playwright test step mapper for SaaS applications.
You understand login flows, dashboards, settings, user accounts, and team management.
Map natural language test steps to CSS selectors, XPath, or accessibility attributes.
Priority: data-testid > aria-label > role > semantic selectors > CSS classes > XPath.""",
            few_shot_examples=[
                "Step: 'I login with email' → Selector: 'input[type=\"email\"]' or 'input[data-testid=\"email-input\"]'",
                "Step: 'I enter my password' → Selector: 'input[type=\"password\"]' or 'input[aria-label=\"Password\"]'",
                "Step: 'I click the login button' → Selector: 'button[type=\"submit\"]' or 'button:has-text(\"Sign In\")'",
                "Step: 'I access dashboard' → Selector: 'div[data-testid=\"dashboard\"]' or 'main:has-text(\"Dashboard\")'",
                "Step: 'I open account settings' → Selector: 'a[href=\"/settings\"]' or 'button[aria-label=\"Settings\"]'",
                "Step: 'I invite team member' → Selector: 'button:has-text(\"Invite\")' or 'a[data-testid=\"invite-user\"]'",
                "Step: 'I logout' → Selector: 'button[aria-label=\"Logout\"]' or 'a:has-text(\"Sign Out\")'",
            ],
            chain_of_thought="""1. Identify element type (button, input, link, etc.)
2. Check for data-testid attribute (highest priority for app stability)
3. Look for aria-label or role attributes (accessibility-first)
4. Try semantic selectors (button:has-text, a[href])
5. Check CSS classes specific to SaaS patterns (nav, sidebar, modal)
6. Use XPath only as last resort""",
        )
        self.templates[Domain.SAAS]["v1"] = saas_v1
        self.templates[Domain.SAAS]["latest"] = saas_v1

        # Fintech templates
        fintech_v1 = PromptTemplate(
            domain=Domain.FINTECH,
            version="v1",
            system_prompt="""You are an expert Playwright test step mapper for fintech applications.
You understand banking forms, account operations, transfers, deposits, and secure transactions.
Map natural language test steps to CSS selectors, XPath, or accessibility attributes.
Prioritize secure, stable selectors for financial workflows.
Priority: data-testid > aria-label > role > semantic selectors > CSS classes > XPath.""",
            few_shot_examples=[
                "Step: 'I view my balance' → Selector: 'span[data-testid=\"account-balance\"]' or 'h2:has-text(\"Balance\")'",
                "Step: 'I initiate a transfer' → Selector: 'button[data-testid=\"transfer-button\"]' or 'a:has-text(\"Transfer Money\")'",
                "Step: 'I enter recipient account' → Selector: 'input[type=\"text\"][aria-label*=\"Account\"]' or 'input[data-testid=\"recipient-account\"]'",
                "Step: 'I enter transfer amount' → Selector: 'input[type=\"number\"][aria-label*=\"Amount\"]' or 'input[data-testid=\"transfer-amount\"]'",
                "Step: 'I confirm transaction' → Selector: 'button[aria-label=\"Confirm\"]' or 'button:has-text(\"Confirm Transfer\")'",
                "Step: 'I view transaction history' → Selector: 'table[data-testid=\"transactions\"]' or 'section:has-text(\"Transaction History\")'",
                "Step: 'I download statement' → Selector: 'button:has-text(\"Download\")' or 'a[data-testid=\"download-statement\"]'",
            ],
            chain_of_thought="""1. Identify element type (button, input, link, table, etc.)
2. Check for data-testid attribute (critical for financial stability)
3. Look for aria-label with amount/account keywords (financial context)
4. Verify element is accessible (role attributes)
5. Use semantic selectors for common patterns (button:has-text)
6. Avoid brittle CSS selectors in fintech (use XPath only if necessary)""",
        )
        self.templates[Domain.FINTECH]["v1"] = fintech_v1
        self.templates[Domain.FINTECH]["latest"] = fintech_v1

        # Generic template (fallback)
        generic_v1 = PromptTemplate(
            domain=Domain.GENERIC,
            version="v1",
            system_prompt="""You are an expert Playwright test step mapper.
Map natural language test steps to CSS selectors, XPath, or accessibility attributes.
Priority: data-testid > aria-label > role > semantic selectors > CSS classes > XPath.""",
            few_shot_examples=[
                "Step: 'I click the button' → Selector: 'button[data-testid=\"action-button\"]' or 'button:has-text(\"Click Me\")'",
                "Step: 'I enter text in input' → Selector: 'input[data-testid=\"text-input\"]' or 'input[aria-label=\"Text Input\"]'",
                "Step: 'I navigate to page' → Selector: 'a[href=\"/page\"]' or 'a:has-text(\"Navigate\")'",
                "Step: 'I see element' → Selector: 'div[data-testid=\"element\"]' or 'div:has-text(\"Element\")'",
                "Step: 'I interact with form' → Selector: 'form[data-testid=\"form\"]' or 'form:has(input[type=\"submit\"])'",
                "Step: 'I wait for load' → Selector: 'div[data-testid=\"loader\"]' or 'span:has-text(\"Loading\")'",
                "Step: 'I verify content' → Selector: 'p:has-text(\"Expected text\")' or 'div[role=\"status\"]'",
            ],
            chain_of_thought="""1. Identify element type
2. Look for data-testid (most stable)
3. Check aria-label and role attributes
4. Use semantic selectors when possible
5. Fall back to CSS classes
6. Use XPath as last resort""",
        )
        self.templates[Domain.GENERIC]["v1"] = generic_v1
        self.templates[Domain.GENERIC]["latest"] = generic_v1

    def get_template(
        self, domain: Domain, version: str = "latest"
    ) -> Optional[PromptTemplate]:
        """
        Retrieve template for domain with optional version pinning.

        Args:
            domain: Domain enum value
            version: Template version (default: "latest")

        Returns:
            PromptTemplate or None if not found
        """
        if domain not in self.templates:
            return None
        if version not in self.templates[domain]:
            return None
        return self.templates[domain][version]

    def add_template(self, template: PromptTemplate) -> bool:
        """
        Add new template version (for A/B testing).

        Args:
            template: PromptTemplate instance to add

        Returns:
            True if added successfully, False if validation fails
        """
        if not template.validate():
            return False

        if template.domain not in self.templates:
            return False

        self.templates[template.domain][template.version] = template
        return True

    def list_versions(self, domain: Domain) -> List[str]:
        """
        List available versions for a domain.

        Args:
            domain: Domain enum value

        Returns:
            List of version strings (e.g., ["v1", "v2", "latest"])
        """
        if domain not in self.templates:
            return []
        return sorted(self.templates[domain].keys())

    def get_system_prompt(
        self, domain: Domain, version: str = "latest"
    ) -> Optional[str]:
        """
        Return formatted system prompt with few-shot examples and chain-of-thought.

        Args:
            domain: Domain enum value
            version: Template version (default: "latest")

        Returns:
            Formatted prompt string or None if template not found
        """
        template = self.get_template(domain, version)
        if not template:
            return None

        # Format: system_prompt + examples + chain_of_thought
        formatted = f"""{template.system_prompt}

Examples:
{chr(10).join(f"  • {example}" for example in template.few_shot_examples)}

Chain of Thought:
{template.chain_of_thought}"""

        return formatted

    def get_full_template(
        self, domain: Domain, version: str = "latest"
    ) -> Optional[PromptTemplate]:
        """Alias for get_template for clarity."""
        return self.get_template(domain, version)
