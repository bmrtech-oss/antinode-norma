from pathlib import Path


def test_ui_dashboard_component_exists():
    component_path = Path("ui/src/components/Dashboard.tsx")
    assert component_path.exists()
    content = component_path.read_text(encoding="utf-8")
    assert "export const Dashboard" in content
    assert "/api/dashboard" in content
    assert 'label: "Total features"' in content
    assert 'label: "Pending approvals"' in content
    assert 'label: "Quality gate pass rate"' in content
    assert 'label: "Audit events"' in content


def test_ui_app_imports_dashboard():
    app_path = Path("ui/src/App.tsx")
    assert app_path.exists()
    content = app_path.read_text(encoding="utf-8")
    assert "import { Dashboard } from './components/Dashboard'" in content
    assert "<Dashboard />" in content
