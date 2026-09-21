"""20 Near-miss golden prompt pairs for Task H3-T02.

These pairs represent semantically distinct user story prompts that share keyword overlap
and must NOT return false-positive semantic cache hits.
"""

NEAR_MISS_GOLDEN_PAIRS = [
    ("User wants to reset password via SMS token", "User wants to reset password via Email link"),
    ("Process payment with Credit Card", "Process payment with Crypto Wallet"),
    ("Search products by price ascending", "Search products by price descending"),
    ("Filter items by available in stock", "Filter items by out of stock"),
    ("Delete user account permanently", "Deactivate user account temporarily"),
    ("Approve feature release request", "Reject feature release request"),
    ("Export user data as CSV file", "Export user data as PDF file"),
    ("Grant admin role to team member", "Revoke admin role from team member"),
    ("Subscribe to monthly billing plan", "Subscribe to annual billing plan"),
    ("Enable 2FA via Authenticator App", "Enable 2FA via SMS verification"),
    ("Upload profile picture as PNG", "Upload profile picture as WEBP"),
    ("Create workspace in EU region", "Create workspace in US region"),
    ("Archive inactive project stories", "Delete inactive project stories"),
    ("Download invoice as PDF", "Email invoice as PDF"),
    ("Notify user via Slack channel", "Notify user via Email digest"),
    ("Set user status to active", "Set user status to suspended"),
    ("Checkout as guest user", "Checkout as registered user"),
    ("Apply 10% discount coupon code", "Apply $10 fixed discount gift card"),
    ("Sort reviews by highest rating", "Sort reviews by newest date"),
    ("Connect database via SQLite", "Connect database via PostgreSQL"),
]
