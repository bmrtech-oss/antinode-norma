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


class ImportResponse(BaseModel):
    id: str
    filename: str
    format: str
    status: str
    row_count: int
    created_at: str
    worksheet_names: List[str] = Field(default_factory=list)
    columns: List[str] = Field(default_factory=list)
    worksheet: Optional[str] = None
    mapping: Dict[str, str] = Field(default_factory=dict)


class ImportValidationResponse(BaseModel):
    import_id: str
    valid: bool
    row_count: int
    errors: List[Dict[str, Any]] = Field(default_factory=list)


class ImportMappingRequest(BaseModel):
    worksheet: Optional[str] = None
    columns: Dict[str, str] = Field(default_factory=dict)


class GenerationJobResponse(BaseModel):
    id: str
    import_id: str
    status: str
    result: Dict[str, Any] = Field(default_factory=dict)
    created_at: str
    total_rows: int = 0
    processed_rows: int = 0
    successful_rows: int = 0
    warning_rows: int = 0
    failed_rows: int = 0
    current_item: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None

    progress_percent: float = 0.0


class GenerationJobRequest(BaseModel):
    import_id: str
