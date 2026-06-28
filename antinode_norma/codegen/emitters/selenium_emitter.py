"""
Selenium (Python) code generator using pytest.
"""

from pathlib import Path
import re

from .base import Emitter
from ..models.test_model import TestSuite, TestStep, ActionType
from ..utils.file_utils import ensure_directory, write_file


class SeleniumEmitter(Emitter):
    """Generate Selenium WebDriver tests in Python (pytest)."""

    def emit(self, suite: TestSuite, output_dir: Path) -> None:
        ensure_directory(output_dir)
        filename = self._safe_filename(suite.name) + "_test.py"
        content = self._render(suite)
        write_file(output_dir / filename, content)

    def _safe_filename(self, name: str) -> str:
        return re.sub(r"[^a-zA-Z0-9_]", "_", name).lower()

    def _render(self, suite: TestSuite) -> str:
        lines = [
            "import pytest",
            "from selenium import webdriver",
            "from selenium.webdriver.common.by import By",
            "from selenium.webdriver.support.ui import WebDriverWait",
            "from selenium.webdriver.support import expected_conditions as EC",
            "",
            f"class Test_{self._safe_filename(suite.name)}:",
            "",
            "    @pytest.fixture(autouse=True)",
            "    def setup(self):",
            "        self.driver = webdriver.Chrome()",
            "        self.driver.implicitly_wait(10)",
            "        yield",
            "        self.driver.quit()",
            "",
        ]
        for case in suite.cases:
            # Define a test method
            method_name = "test_" + self._safe_filename(case.name)
            lines.append(f"    def {method_name}(self):")
            for step in case.steps:
                lines.append(f"        {self._translate_step(step)}")
            lines.append("")
        return "\n".join(lines)

    def _translate_step(self, step: TestStep) -> str:
        action = step.action
        target = step.target
        value = step.value
        if action == ActionType.NAVIGATE:
            return f"self.driver.get('{value}')"
        elif action == ActionType.CLICK:
            return f"self.driver.find_element(By.CSS_SELECTOR, '{target}').click()"
        elif action == ActionType.FILL:
            return f"self.driver.find_element(By.CSS_SELECTOR, '{target}').send_keys('{value}')"
        elif action == ActionType.ASSERT_TEXT:
            return f"assert '{value}' in self.driver.page_source"
        elif action == ActionType.ASSERT_VISIBLE:
            return f"assert self.driver.find_element(By.CSS_SELECTOR, '{target}').is_displayed()"
        elif action == ActionType.ASSERT_HIDDEN:
            return f"assert not self.driver.find_element(By.CSS_SELECTOR, '{target}').is_displayed()"
        elif action == ActionType.WAIT:
            return f"import time; time.sleep({int(value)})"
        elif action == ActionType.CHECK:
            return f"self.driver.find_element(By.CSS_SELECTOR, '{target}').click()  # assuming checkbox"
        elif action == ActionType.UNCHECK:
            return "# Uncheck not directly supported, click again if needed"
        elif action == ActionType.SELECT:
            return f"from selenium.webdriver.support.ui import Select; Select(self.driver.find_element(By.CSS_SELECTOR, '{target}')).select_by_visible_text('{value}')"
        elif action == ActionType.ASSERT_URL:
            return f"assert self.driver.current_url == '{value}'"
        elif action == ActionType.ASSERT_TITLE:
            return f"assert self.driver.title == '{value}'"
        else:
            return f"# UNKNOWN: {step.description}"
