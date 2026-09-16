"""Feature viewer routes for Norma BDD Platform FastAPI server."""

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from antinode_norma.server.schemas import FeatureSummary, FeatureDetail
from antinode_norma.gates.runner import GateRunner
from antinode_norma.gates.types import GateContext

router = APIRouter(prefix="/api/features", tags=["Features"])


def _get_feature_dir() -> Path:
    """Returns configured or default feature directory path."""
    feature_dir = os.environ.get("NORMA_FEATURE_DIR", "features")
    return Path(feature_dir)


def _parse_scenarios(content: str) -> List[str]:
    """Extracts scenario titles from Gherkin feature content."""
    scenarios = []
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("Scenario:") or stripped.startswith("Scenario Outline:"):
            title = stripped.split(":", 1)[1].strip()
            scenarios.append(title)
    return scenarios


@router.get("", response_model=List[FeatureSummary])
async def list_features(dir_override: Optional[str] = Query(None, alias="dir")) -> List[FeatureSummary]:
    """Lists all .feature files in the feature directory."""
    feature_dir = Path(dir_override) if dir_override else _get_feature_dir()
    if not feature_dir.exists() or not feature_dir.is_dir():
        return []

    summaries: List[FeatureSummary] = []
    for path in sorted(feature_dir.glob("*.feature")):
        try:
            content = path.read_text(encoding="utf-8")
            scenarios = _parse_scenarios(content)
            mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
            summaries.append(
                FeatureSummary(
                    filename=path.name,
                    path=str(path),
                    scenario_count=len(scenarios),
                    modified_at=mtime,
                )
            )
        except Exception:
            continue

    return summaries


@router.get("/{filename}", response_model=FeatureDetail)
async def get_feature_detail(
    filename: str,
    dir_override: Optional[str] = Query(None, alias="dir"),
    run_gates: bool = Query(False),
) -> FeatureDetail:
    """Retrieves details, Gherkin content, scenarios, and optional gate results for a feature file."""
    feature_dir = Path(dir_override) if dir_override else _get_feature_dir()
    file_path = feature_dir / filename

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail=f"Feature file '{filename}' not found.")

    content = file_path.read_text(encoding="utf-8")
    scenarios = _parse_scenarios(content)

    gate_results = None
    if run_gates:
        try:
            ctx = GateContext(gherkin_text=content)
            runner = GateRunner()
            verdict = runner.evaluate(ctx)
            gate_results = {
                "summary": verdict.summary,
                "hard_pass": verdict.hard_pass,
                "soft_score": verdict.soft_score,
                "sem_score": verdict.sem_score,
            }
        except Exception:
            gate_results = None

    return FeatureDetail(
        filename=filename,
        path=str(file_path),
        content=content,
        scenarios=scenarios,
        gate_results=gate_results,
    )
