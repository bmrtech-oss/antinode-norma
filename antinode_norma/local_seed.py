"""Deterministic local development seed data for ADR-013."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_SEED_ROOT = Path(".runtime/local-seed")
SEED_VERSION = "2026-09-25.v1"

USERS = [
    {"id": "seed-admin", "username": "admin", "email": "admin@local.test", "roles": ["admin"]},
    {"id": "seed-reviewer", "username": "reviewer", "email": "reviewer@local.test", "roles": ["reviewer"]},
    {"id": "seed-generator", "username": "generator", "email": "generator@local.test", "roles": ["generator"]},
    {"id": "seed-viewer", "username": "viewer", "email": "viewer@local.test", "roles": ["viewer"]},
]

APPROVALS = [
    {"id": "seed-approval-pending", "feature_id": "seed-login", "status": "PENDING"},
    {"id": "seed-approval-approved", "feature_id": "seed-reset", "status": "APPROVED"},
    {"id": "seed-approval-rejected", "feature_id": "seed-export", "status": "REJECTED"},
]

FEATURES = {
    "seed-login.feature": "Feature: Seed Login\n\n  @seed-login\n  Scenario: Login as a reviewer\n    Given the reviewer is on the login page\n    When the reviewer submits valid credentials\n    Then the reviewer sees the dashboard\n",
    "seed-reset.feature": "Feature: Seed Password Reset\n\n  @seed-reset\n  Scenario: Reset a password\n    Given the user requests a reset link\n    When the user submits a new password\n    Then the password is updated\n",
    "seed-export.feature": "Feature: Seed Export\n\n  @seed-export\n  Scenario: Export a report\n    Given the generator has report data\n    When the generator exports the report\n    Then a CSV file is downloaded\n",
}


def seed_local(
    root: Path = DEFAULT_SEED_ROOT,
    reset: bool = False,
    database_url: str | None = None,
) -> dict[str, Any]:
    """Create or refresh deterministic local state without network calls."""
    if reset and root.exists():
        for child in root.iterdir():
            if child.is_dir():
                import shutil

                shutil.rmtree(child)
            else:
                child.unlink()

    root.mkdir(parents=True, exist_ok=True)
    _write_json(root / "users.json", USERS)
    _write_json(root / "approvals.json", APPROVALS)
    for filename, content in FEATURES.items():
        feature_path = root / "features" / filename
        feature_path.parent.mkdir(parents=True, exist_ok=True)
        feature_path.write_text(content, encoding="utf-8")
    _write_json(root / "traceability.json", {"covered": ["seed-login", "seed-reset"], "uncovered": ["seed-export"]})
    _write_json(root / "audit.json", [{"id": "seed-audit-1", "action": "seed.completed", "actor": "system"}])
    _write_json(root / "analytics.json", {"features": 3, "approvals": 3, "audit_events": 1})
    _write_json(root / "execution_history.json", [{"id": "seed-run-1", "status": "PASSED", "total_scenarios": 3}])
    _write_json(root / "plugins.json", [{"name": "seed-plugin", "permissions": ["read:features"]}])
    _write_json(root / "notifications.json", [{"event_type": "seed.completed", "channel": "email", "recipient": "reviewer@local.test"}])
    _write_json(
        root / "manifest.json",
        {
            "version": SEED_VERSION,
            "provider": "mock",
            "fixture_counts": {"users": len(USERS), "approvals": len(APPROVALS), "features": len(FEATURES)},
        },
    )
    marker = {
        "seed_version": SEED_VERSION,
        "fixture_counts": {"users": len(USERS), "approvals": len(APPROVALS), "features": len(FEATURES)},
    }
    if database_url:
        from antinode_norma.database import seed_auth_users, seed_database

        marker["database_records"] = seed_database(root, database_url)
        marker["database_auth_users"] = seed_auth_users(database_url)
    _write_json(Path(".runtime/local-seed-complete.json"), marker)
    return marker


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")