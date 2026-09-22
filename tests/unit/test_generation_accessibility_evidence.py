"""Focused static evidence checks for the generation workflow's accessibility contract."""

from pathlib import Path


ROOT = Path(__file__).parents[2]


def test_generation_upload_and_status_controls_have_accessibility_evidence():
    content = (ROOT / "ui" / "src" / "components" / "Generation.tsx").read_text(encoding="utf-8")
    assert 'type="file"' in content
    assert 'accept=".csv,.xlsx' in content
    assert 'aria-live="assertive"' in content
    assert 'aria-label={`Generation progress' in content


def test_app_shell_exposes_keyboard_navigation_and_skip_link():
    content = (ROOT / "ui" / "src" / "components" / "AppShell.tsx").read_text(encoding="utf-8")
    assert 'href="#main-content"' in content
    assert 'aria-label="Primary navigation"' in content
    assert 'role="tablist"' in content
