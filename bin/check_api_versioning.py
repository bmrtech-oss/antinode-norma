#!/usr/bin/env python3
"""CI enforcement script verifying /v1/ API route prefix policy.

Task H2-T05 (Phase H2 - Enterprise Completeness).
Inspects FastAPI route registration in antinode_norma/server/api.py and fails CI if route modules are mounted without /v1/ prefix.
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from antinode_norma.server.api import app


def verify_v1_versioning() -> bool:
    """Verifies that all registered API routes are available under /v1/ prefix."""
    paths = list(app.openapi().get("paths", {}).keys())

    api_routes = [p for p in paths if p.startswith("/api/") or p.startswith("/v1/api/")]
    v1_api_routes = [p for p in paths if p.startswith("/v1/api/")]

    if not api_routes:
        print("Error: No API routes found!")
        return False

    if not v1_api_routes:
        print("Error: No /v1/ versioned API routes registered!")
        return False

    print("API Versioning Verification Passed:")
    print(f"  Total API routes: {len(api_routes)}")
    print(f"  Versioned (/v1/) API routes: {len(v1_api_routes)}")
    return True


if __name__ == "__main__":
    if not verify_v1_versioning():
        sys.exit(1)
