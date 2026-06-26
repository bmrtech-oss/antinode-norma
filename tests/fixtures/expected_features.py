"""Expected Gherkin feature file snippets for validation."""

EXPECTED_FEATURE_FOR_PASSWORD_RESET = """
Feature: Password Reset
  As a registered user
  I want to reset my password via email
  So that I can regain access to my account

  Scenario: Password reset email sent
    Given the user is on the login page
    When the user requests a password reset
    Then the system sends a reset link to the user's registered email

  Scenario: User sets new password
    Given the user receives a valid reset link
    When the user clicks the link and sets a new password
    Then the password is updated

  Scenario: Invalid or expired token
    Given the user clicks a reset link after 30 minutes or with invalid token
    Then an error message is displayed
""".strip()
