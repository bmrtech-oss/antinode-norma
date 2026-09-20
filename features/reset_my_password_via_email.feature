Feature: Reset my password via email

  Scenario: Generate a feature for reset my password via email
    Given the registered user, is on the system page
    When they reset my password via email
    Then the outcome should support I can regain access to my account. Acceptance criteria: - The system should send a password reset link to the user's registered email. - The user should be able to click the link and set a new password. - The system should display an error message when an invalid token is used. - The system should expire the reset link after 30 minutes.
