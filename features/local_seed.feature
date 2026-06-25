Feature: Local seed flow for antinode-norma
  As a registered user
  I want to reset my password so that I can regain access to my account
  So that I can recover when I forget my password

  Scenario: Reset password from login page
    Given I am on the login page
    When I click the "Forgot Password" link
    And I submit my registered email address
    Then I receive a password reset email
    And I open the reset link
    And I set a new password
    And I can log in with the new password successfully
