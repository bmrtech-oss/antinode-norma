Feature: Password Reset

  As a user
  I want to reset my password
  So that I can regain access to my account

  Scenario: Successful password reset
    Given the user is on the login page
    When the user clicks 'Forgot password'
    Then a password reset email is sent
    Given a valid reset token exists
    When the user submits a new password
    Then the password is updated

  Scenario: Invalid reset token
    Given the user is on the login page
    When the user clicks 'Forgot password'
    Then a password reset email is sent
    Given an invalid reset token exists
    When the user submits a new password
    Then the system should display an error message for invalid tokens

  Scenario: No reset token provided
    Given the user is on the login page
    When the user clicks 'Forgot password'
    Then a password reset email is sent
    When the user attempts to submit a new password without a token
    Then the system should display an error message for invalid tokens