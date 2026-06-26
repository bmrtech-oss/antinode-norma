"""Sample stories for testing (can be imported in other test files)."""

PASSING_STORY = """
As a registered user, I want to reset my password via email so that
I can regain access to my account.
Acceptance criteria:
- The system should send a password reset link to the user's registered email.
- The user should be able to click the link and set a new password.
- The system should display an error message when an invalid token is used.
- The system should expire the reset link after 30 minutes.
"""

FAILING_STORY = "User wants to reset password."
