# Feature: Password reset via email for registered users
# This feature covers requesting a reset link, using a valid token, handling an invalid token,
# and ensuring the reset link expires after 30 minutes.

Feature: Password reset

  Scenario: Request password reset link
    Given the user is on the login page
    When the user clicks 'Forgot password'
    Then a password reset email is sent

  Scenario: Reset password with a valid token
    Given a valid reset token exists
    When the user submits a new password
    Then the password is updated

  Scenario: Show error for invalid token
    Given the user has an invalid reset token
    When the user attempts to reset the password
    Then the system displays an invalid token error message

  Scenario: Expired reset link cannot be used
    Given a valid reset token exists
    And the reset token is older than 30 minutes
    When the user attempts to reset the password
    Then the system displays a token expired error message