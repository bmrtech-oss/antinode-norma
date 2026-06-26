Feature: Password reset for registered users

  As a registered user
  I want to reset my password
  So that I can regain access to my account

  Scenario: Forgot Password link is displayed on the login page
    Given the user is on the login page
    Then the system returns a "Forgot Password" link on the login page

  Scenario: Receive password reset email within 2 minutes
    Given the user is on the login page
    When the user clicks 'Forgot password'
    And the user submits a registered email address
    Then a password reset email is sent
    And the email is received within 2 minutes

  Scenario: Reset link is secure and expires after 1 hour
    Given a valid reset token exists
    When the user clicks the reset link in the email
    Then the reset link is secure
    And the reset link expires in 1 hour

  Scenario: Set a new password and receive confirmation
    Given a valid reset token exists
    When the user submits a new password
    Then the password is updated
    And the system returns a confirmation that the new password is set

  Scenario: Login with the new password
    Given the user has successfully updated the password
    When the user logs in with the new password
    Then the system returns a successful login session with the new password