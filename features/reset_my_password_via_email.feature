# Feature: Password reset via email for registered users
# This feature covers sending the reset link, using a valid token, handling invalid tokens,
# and ensuring the reset link expires after 30 minutes.

Feature: Password reset

  Background:
    Given the user is on the login page

  Scenario: Request password reset link
    When the user clicks 'Forgot password'
    Then a password reset email is sent

  Scenario: Reset password with a valid token
    Given a valid reset token exists
    When the user submits a new password
    Then the password is updated

  Scenario: Show error for invalid token
    Given an invalid reset token exists
    When the user attempts to reset the password
    Then the system displays an invalid token error message

  Scenario: Expired reset link after 30 minutes
    Given a valid reset token exists
    And the reset token is older than 30 minutes
    When the user attempts to reset the password
    Then the system displays a token expired error message