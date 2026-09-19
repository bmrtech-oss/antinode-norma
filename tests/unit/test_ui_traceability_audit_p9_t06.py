"""Unit tests for Phase 9 Task P9-T06: Frontend Traceability & Audit Components."""

import unittest
from pathlib import Path


class TestUITraceabilityAuditPage(unittest.TestCase):
    def setUp(self):
        self.ui_dir = Path("ui")

    def test_components_exist(self):
        trace_comp = self.ui_dir / "src" / "components" / "TraceabilityView.tsx"
        self.assertTrue(trace_comp.exists())
        trace_content = trace_comp.read_text(encoding="utf-8")
        self.assertIn("export default function TraceabilityView", trace_content)
        self.assertIn("/api/traceability", trace_content)

        audit_comp = self.ui_dir / "src" / "components" / "AuditTrailView.tsx"
        self.assertTrue(audit_comp.exists())
        audit_content = audit_comp.read_text(encoding="utf-8")
        self.assertIn("export default function AuditTrailView", audit_content)
        self.assertIn("/api/audit", audit_content)
        self.assertIn("/api/audit/verify", audit_content)

    def test_app_navigation_integration(self):
        app = self.ui_dir / "src" / "App.tsx"
        self.assertTrue(app.exists())

        content = app.read_text(encoding="utf-8")
        self.assertIn("import TraceabilityView from './components/TraceabilityView'", content)
        self.assertIn("import AuditTrailView from './components/AuditTrailView'", content)
        self.assertIn("Traceability", content)
        self.assertIn("Audit Log", content)


if __name__ == "__main__":
    unittest.main()
