"""Traceability matrix routes for Norma BDD Platform FastAPI server."""

import os
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Query

from antinode_norma.governance.traceability import TraceabilityRenderer, TraceabilityMatrix

router = APIRouter(prefix="/api/traceability", tags=["Traceability"])


def _get_feature_dir() -> Path:
    feature_dir = os.environ.get("NORMA_FEATURE_DIR", "features")
    return Path(feature_dir)


@router.get("", response_model=TraceabilityMatrix)
async def get_traceability_matrix(dir_override: Optional[str] = Query(None, alias="dir")) -> TraceabilityMatrix:
    """Generates and returns requirement-to-scenario traceability matrix."""
    feature_dir = Path(dir_override) if dir_override else _get_feature_dir()

    combined_text = []
    if feature_dir.exists() and feature_dir.is_dir():
        for path in sorted(feature_dir.glob("*.feature")):
            try:
                combined_text.append(path.read_text(encoding="utf-8"))
            except Exception:
                continue

    gherkin_text = "\n\n".join(combined_text)
    matrix = TraceabilityRenderer.build_matrix(gherkin_text=gherkin_text)
    matrix.feature_title = f"All Features ({len(combined_text)} files)"
    return matrix
