Feature: Password reset via email

  As a registered user
  I want to reset my password using a link sent to my email
  So that I can regain access to my account

  @smoke
  Scenario: Successful password reset within token validity period
    Given the user is on the login page
    When the user clicks 'Forgot password'
    Then a password reset email is sent
    Given a valid reset token exists
    When the user clicks the password reset link
    And the user submits a new password
    Then the password is updated

  Scenario: Attempt to reset password with an invalid token
    Given the user is on the login page
    When the user clicks 'Forgot password'
    Then a password reset email is sent
    Given an invalid reset token exists
    When the user clicks the password reset link
    Then the system should display an error message "Invalid or expired token"

  Scenario: Reset link expires after 30 minutes
    Given the user is on the login page
    When the user clicks 'Forgot password'
    Then a password reset email is sent
    Given a valid reset token exists
    And the token is older than 30 minutes
    When the user clicks the password reset link
    Then the system should display an error message "Invalid or expired token"