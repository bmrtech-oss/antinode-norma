# Feature: Password reset via email
# This feature covers sending the reset link, using a valid token,
# handling an invalid token, and ensuring the link expires after 30 minutes.

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

  Scenario: Expire reset link after 30 minutes
    Given a valid reset token exists
    And 31 minutes have passed since the token was issued
    When the user attempts to reset the password
    Then the system displays a token expired error message