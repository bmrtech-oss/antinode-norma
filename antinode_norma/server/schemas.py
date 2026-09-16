"""API schemas for Antinode Norma FastAPI server."""

from datetime import datetime, timezone
from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str = "ok"
    version: str = "0.1.0"
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ErrorResponse(BaseModel):
    """Standard error response schema."""
    detail: str
    error_code: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class FeatureSummary(BaseModel):
    """Summary representation of a Gherkin feature file."""
    filename: str
    path: str
    scenario_count: int = 0
    modified_at: str


class FeatureDetail(BaseModel):
    """Detailed view of a Gherkin feature file."""
    filename: str
    path: str
    content: str
    scenarios: List[str] = Field(default_factory=list)
    gate_results: Optional[Dict[str, Any]] = None
