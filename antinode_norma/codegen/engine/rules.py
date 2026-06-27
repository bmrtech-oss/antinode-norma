"""
Declarative rules for mapping Gherkin step text to generic actions.
"""

import re
from typing import Optional, Tuple, Dict, Any, Callable, List
from ..config import get_config
from ..models.test_model import ActionType


class RuleEngine:
    def __init__(self):
        self.rules: List[Tuple[re.Pattern, ActionType,
                               Callable, Callable, Callable]] = []
        self._compile_default_rules()

    def _compile_default_rules(self):
        # --- NAVIGATE ---
        self.add_rule(
            r"^(?:Given |And )?I (?:navigate to|open|go to) \"(?P<url>[^\"]*)\"",
            ActionType.NAVIGATE,
            lambda m: None,
            lambda m: m.group("url"),
            lambda m: {},
        )

        self.add_rule(
            r"^(?:Given |And )?the user is on the (?P<page>[^\"]*) page",
            ActionType.NAVIGATE,
            lambda m: None,
            lambda m: self._page_url(m.group("page")),
            lambda m: {},
        )
        self.add_rule(
            r"^(?:Given |And )?I am on the (?P<page>[^\"]*) page",
            ActionType.NAVIGATE,
            lambda m: None,
            lambda m: self._page_url(m.group("page")),
            lambda m: {},
        )

        # --- CLICK ---
        self.add_rule(
            r"^(?:When |And )?I (?:click|tap) (?:on )?\"(?P<selector>[^\"]*)\"",
            ActionType.CLICK,
            lambda m: m.group("selector"),
            lambda m: None,
            lambda m: {},
        )
        self.add_rule(
            r"^(?:When |And )?the user clicks '(?P<text>[^']*)'",
            ActionType.CLICK,
            lambda m: f"text={m.group('text')}",
            lambda m: None,
            lambda m: {},
        )
        self.add_rule(
            r"^(?:When |And )?the user clicks the (?P<element>.*)",
            ActionType.CLICK,
            lambda m: f"text={m.group('element')}",
            lambda m: None,
            lambda m: {},
        )
        self.add_rule(
            r"^(?:When |And )?I click the \"(?P<text>[^\"]*)\" (?:link|button)",
            ActionType.CLICK,
            lambda m: f"text={m.group('text')}",
            lambda m: None,
            lambda m: {},
        )
        self.add_rule(
            r"^(?:And )?I open the (?P<link_type>\w+) link",
            ActionType.CLICK,
            lambda m: f"text={m.group('link_type')} link",
            lambda m: None,
            lambda m: {},
        )

        # --- FILL ---
        self.add_rule(
            r"^(?:When |And )?I (?:fill|enter|type) \"(?P<value>[^\"]*)\" into \"(?P<selector>[^\"]*)\"",
            ActionType.FILL,
            lambda m: m.group("selector"),
            lambda m: m.group("value"),
            lambda m: {},
        )
        self.add_rule(
            r"^(?:When |And )?I fill \"(?P<value>[^\"]*)\" in \"(?P<selector>[^\"]*)\"",
            ActionType.FILL,
            lambda m: m.group("selector"),
            lambda m: m.group("value"),
            lambda m: {},
        )
        self.add_rule(
            r"^(?:When |And )?I submit (?:my )?registered email address",
            ActionType.FILL,
            lambda m: "#email",
            lambda m: "user@example.com",
            lambda m: {},
        )
        self.add_rule(
            r"^(?:When |And )?the user submits a registered email address",
            ActionType.FILL,
            lambda m: "#email",
            lambda m: "user@example.com",
            lambda m: {},
        )
        self.add_rule(
            r"^(?:When |And )?I set a new password",
            ActionType.FILL,
            lambda m: "#new-password",
            lambda m: "new_secure_password",
            lambda m: {},
        )
        self.add_rule(
            r"^(?:When |And )?the user submits a new password",
            ActionType.FILL,
            lambda m: "#new-password",
            lambda m: "new_secure_password",
            lambda m: {},
        )

        # --- LOGIN (new) ---
        # Map "logs in with the new password" to a NAVIGATE to dashboard
        self.add_rule(
            r"^(?:And )?I can log in with the new password successfully",
            ActionType.NAVIGATE,
            lambda m: None,
            lambda m: self._page_url("dashboard"),
            lambda m: {},
        )
        self.add_rule(
            r"^(?:When |And )?the user logs in with the new password",
            ActionType.NAVIGATE,
            lambda m: None,
            lambda m: self._page_url("dashboard"),
            lambda m: {},
        )

        # --- ASSERTIONS ---
        self.add_rule(
            r"^(?:Then |And )?the system should display an error message \"(?P<text>[^\"]*)\"",
            ActionType.ASSERT_TEXT,
            lambda m: None,
            lambda m: m.group("text"),
            lambda m: {},
        )
        self.add_rule(
            r"^(?:Then |And )?I should see \"(?P<text>[^\"]*)\"",
            ActionType.ASSERT_TEXT,
            lambda m: None,
            lambda m: m.group("text"),
            lambda m: {},
        )
        self.add_rule(
            r"^(?:Then |And )?the system returns a \"(?P<text>[^\"]*)\"",
            ActionType.ASSERT_TEXT,
            lambda m: None,
            lambda m: m.group("text"),
            lambda m: {},
        )
        self.add_rule(
            r"^(?:Then |And )?I receive a password reset email",
            ActionType.ASSERT_TEXT,
            lambda m: None,
            lambda m: "password reset email",
            lambda m: {},
        )
        self.add_rule(
            r"^(?:Then |And )?a password reset email is sent",
            ActionType.ASSERT_TEXT,
            lambda m: None,
            lambda m: "reset email sent",
            lambda m: {},
        )
        self.add_rule(
            r"^(?:Then |And )?the email is received within \d+ minutes?",
            ActionType.ASSERT_TEXT,
            lambda m: None,
            lambda m: "email received",
            lambda m: {},
        )
        self.add_rule(
            r"^(?:Then |And )?the reset link is secure",
            ActionType.ASSERT_TEXT,
            lambda m: None,
            lambda m: "reset link secure",
            lambda m: {},
        )
        self.add_rule(
            r"^(?:Then |And )?the reset link expires in \d+ hours?",
            ActionType.ASSERT_TEXT,
            lambda m: None,
            lambda m: "reset link expires",
            lambda m: {},
        )
        self.add_rule(
            r"^(?:Then |And )?the password is updated",
            ActionType.ASSERT_TEXT,
            lambda m: None,
            lambda m: "password updated",
            lambda m: {},
        )
        self.add_rule(
            r"^(?:Then |And )?the system returns a confirmation that the new password is set",
            ActionType.ASSERT_TEXT,
            lambda m: None,
            lambda m: "password set confirmation",
            lambda m: {},
        )
        self.add_rule(
            r"^(?:Then |And )?the system returns a successful login session with the new password",
            ActionType.ASSERT_TEXT,
            lambda m: None,
            lambda m: "login successful",
            lambda m: {},
        )

        # --- URL ASSERTIONS ---
        self.add_rule(
            r"^(?:Then |And )?the URL should be \"(?P<url>[^\"]*)\"",
            ActionType.ASSERT_URL,
            lambda m: None,
            lambda m: m.group("url"),
            lambda m: {},
        )

        # --- VISIBILITY ---
        self.add_rule(
            r"^(?:Then |And )?\"(?P<selector>[^\"]*)\" should be visible",
            ActionType.ASSERT_VISIBLE,
            lambda m: m.group("selector"),
            lambda m: None,
            lambda m: {},
        )
        self.add_rule(
            r"^(?:Then |And )?\"(?P<selector>[^\"]*)\" should not be visible",
            ActionType.ASSERT_HIDDEN,
            lambda m: m.group("selector"),
            lambda m: None,
            lambda m: {},
        )

        # --- WAIT ---
        self.add_rule(
            r"^(?:Given |And )?the token is older than \d+ minutes?",
            ActionType.WAIT,
            lambda m: None,
            lambda m: "31",
            lambda m: {},
        )
        self.add_rule(
            r"^(?:And )?I wait for (?P<seconds>\d+) seconds?",
            ActionType.WAIT,
            lambda m: None,
            lambda m: m.group("seconds"),
            lambda m: {},
        )

        # --- CHECK / UNCHECK ---
        self.add_rule(
            r"^(?:When |And )?I check \"(?P<selector>[^\"]*)\"",
            ActionType.CHECK,
            lambda m: m.group("selector"),
            lambda m: None,
            lambda m: {},
        )
        self.add_rule(
            r"^(?:When |And )?I uncheck \"(?P<selector>[^\"]*)\"",
            ActionType.UNCHECK,
            lambda m: m.group("selector"),
            lambda m: None,
            lambda m: {},
        )

        # --- SELECT ---
        self.add_rule(
            r"^(?:When |And )?I select \"(?P<value>[^\"]*)\" from \"(?P<selector>[^\"]*)\"",
            ActionType.SELECT,
            lambda m: m.group("selector"),
            lambda m: m.group("value"),
            lambda m: {},
        )

        # --- GIVEN SETUP (dummy) ---
        self.add_rule(
            r"^(?:Given )?an invalid reset token exists",
            ActionType.NAVIGATE,
            lambda m: None,
            lambda m: self._url_with_path("/reset?token=invalid"),
            lambda m: {},
        )
        self.add_rule(
            r"^(?:Given )?a valid reset token exists",
            ActionType.NAVIGATE,
            lambda m: None,
            lambda m: self._url_with_path("/reset"),
            lambda m: {},
        )
        self.add_rule(
            r"^(?:Given )?the user has successfully updated the password",
            ActionType.NAVIGATE,
            lambda m: None,
            lambda m: self._base_url(),
            lambda m: {},
        )

    def _base_url(self) -> str:
        config_url = get_config().base_url
        if config_url:
            return config_url.rstrip("/")
        return "https://example.com"

    def _page_url(self, page: Optional[str]) -> str:
        base = self._base_url()
        if not page:
            return base
        page_path = page.strip().replace(" ", "_")
        return f"{base}/{page_path}"

    def _url_with_path(self, path: str) -> str:
        base = self._base_url()
        trimmed = path.lstrip("/")
        return f"{base}/{trimmed}"

    def add_rule(
        self,
        pattern: str,
        action: ActionType,
        target_func: Callable,
        value_func: Callable,
        options_func: Callable,
    ):
        self.rules.append(
            (re.compile(pattern),
             action,
             target_func,
             value_func,
             options_func))

    def map_step(
        self, step_text: str
    ) -> Tuple[ActionType, Optional[str], Optional[str], Dict[str, Any]]:
        for pattern, action, target_func, value_func, options_func in self.rules:
            match = pattern.match(step_text)
            if match:
                target = target_func(match) if target_func else None
                value = value_func(match) if value_func else None
                options = options_func(match) if options_func else {}
                return action, target, value, options
        raise ValueError(f"No rule matches step: {step_text}")
