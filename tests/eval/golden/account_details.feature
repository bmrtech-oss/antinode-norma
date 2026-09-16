@TC-101 @TC-102
Feature: Account Details Management
  As a registered user
  I want to view and update my account details
  So that my profile information remains accurate

  @TC-101 @smoke
  Scenario: View account details
    Given the user is logged in to their account
    When the user navigates to the account details page
    Then the page displays the user's name, email, and member status

  @TC-102
  Scenario: Update contact email address
    Given the user is on the account details page
    When the user updates their email address and clicks save
    Then a confirmation message is displayed
    And the new email address is saved to the profile
