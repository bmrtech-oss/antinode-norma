Feature: User Login
  As a registered user
  I want to log in to the application
  So that I can access my dashboard

  Background:
    Given I navigate to "https://example.com/login"

  Scenario: Successful login with valid credentials
    When I fill "testuser@example.com" into "#email"
    And I fill "SecurePass123" into "#password"
    And I click on "#login-button"
    Then I should see "Welcome back, Test User"
    And the URL should be "https://example.com/dashboard"

  Scenario: Failed login with invalid password
    When I fill "testuser@example.com" into "#email"
    And I fill "WrongPass" into "#password"
    And I click on "#login-button"
    Then I should see "Invalid credentials"
    And the URL should be "https://example.com/login"
