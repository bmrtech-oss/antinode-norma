from typing import List
from .schemas import UserStory

FEATURE_GENERATION_EXAMPLES = [
    {
        "role": "registered user",
        "action": "reset password via email",
        "benefit": "regain access to my account",
        "acceptance_criteria": [
            "The system sends a password reset link to the registered email.",
            "The user can click the link and set a new password.",
            "Invalid reset tokens show an error message.",
        ],
        "feature": "Feature: Password reset\n\nScenario: Request password reset link\n  Given the user is on the login page\n  When the user requests a password reset link\n  Then the system sends a reset email to the registered address\n\nScenario: Reset password with valid token\n  Given the user has a valid reset token\n  When the user submits a new password\n  Then the password is updated successfully\n\nScenario: Show error for invalid token\n  Given the user has an invalid reset token\n  When the user attempts to reset the password\n  Then the system displays an invalid token error message"
    },
    {
        "role": "online shopper",
        "action": "purchase items from the cart",
        "benefit": "complete checkout quickly",
        "acceptance_criteria": [
            "The cart summary is displayed with item prices.",
            "The user can enter shipping and payment details.",
            "The order confirmation page is shown after payment.",
        ],
        "feature": "Feature: Checkout order\n\nScenario: Review cart before purchase\n  Given the shopper has items in their cart\n  When they view the cart summary\n  Then the page shows item names, quantities, and total price\n\nScenario: Complete checkout with payment\n  Given the shopper is on the checkout page\n  When they enter shipping and payment information and submit\n  Then the order confirmation page is displayed"
    },
    {
        "role": "guest shopper",
        "action": "search for products",
        "benefit": "find items quickly",
        "acceptance_criteria": [
            "The search bar accepts keywords.",
            "Search results show matching products.",
            "The user can filter results by category.",
        ],
        "feature": "Feature: Product search\n\nScenario: Search using keywords\n  Given the shopper is on the homepage\n  When they enter a product keyword in the search bar\n  Then search results display matching products\n\nScenario: Filter search results\n  Given search results are visible\n  When the shopper filters by category\n  Then the results list is updated to match the selected category"
    },
]

FEATURE_PROMPT_TEMPLATE = """You are a BDD expert and writer. Analyze the story below and the acceptance criteria.

1. Identify the scenarios needed to fully cover the acceptance criteria.
2. Write a valid Gherkin .feature file that includes clear Given/When/Then steps.
3. If you include reasoning, prepend it only with '#' comments before the Feature section.
4. Use the examples below as inspiration for structure, clarity, and scenario coverage.

Examples:
{examples}

Story:
Role: {role}
Action: {action}
Benefit: {benefit}
Acceptance criteria:
{criteria}

Output ONLY a valid Gherkin feature file. Do not include analysis outside of comment lines."""

VALIDATE_GHERKIN_PROMPT = """You are a Gherkin expert. Check whether the following feature file is valid and complete:

{feature}

Return only 'valid' or 'invalid' with a short justification."""

INVEST_PROMPT = """You are a story quality expert. Assess the following user story for INVEST criteria.

Story:
{story}

Return a JSON object with keys: independent, negotiable, valuable, estimable, small, testable."""


def select_feature_examples(story: UserStory) -> List[str]:
    keywords = story.action.lower() + " " + story.benefit.lower()
    examples = []
    if "reset" in keywords or "password" in keywords or "login" in keywords:
        examples.append(FEATURE_GENERATION_EXAMPLES[0]["feature"])
    if "checkout" in keywords or "cart" in keywords or "payment" in keywords:
        examples.append(FEATURE_GENERATION_EXAMPLES[1]["feature"])
    if "search" in keywords or "product" in keywords or "filter" in keywords:
        examples.append(FEATURE_GENERATION_EXAMPLES[2]["feature"])
    if not examples:
        examples = [ex["feature"] for ex in FEATURE_GENERATION_EXAMPLES[:2]]
    return examples
