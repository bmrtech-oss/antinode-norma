"""Unit tests for Phase 9 Task P9-T05: Frontend Approval Queue Component."""

import unittest
from pathlib import Path


class TestUIApprovalQueuePage(unittest.TestCase):
    def setUp(self):
        self.ui_dir = Path("ui")

    def test_approval_queue_component_exists(self):
        comp = self.ui_dir / "src" / "components" / "ApprovalQueue.tsx"
        self.assertTrue(comp.exists())

        content = comp.read_text(encoding="utf-8")
        self.assertIn("export default function ApprovalQueue", content)
        self.assertIn("/api/approvals", content)
        self.assertIn("Governance Approval Queue", content)

    def test_app_navigation_integration(self):
        app_shell = self.ui_dir / "src" / "components" / "AppShell.tsx"
        self.assertTrue(app_shell.exists())

        content = app_shell.read_text(encoding="utf-8")
        self.assertIn("Approval Queue", content)


if __name__ == "__main__":
    unittest.main()
