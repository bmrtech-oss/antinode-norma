from pydantic import BaseModel, Field, field_validator
from typing import List, Optional


class UserStory(BaseModel):
    raw_text: str = ""
    role: str
    action: str
    benefit: str
    acceptance_criteria: List[str] = Field(min_length=1)
    dependencies: Optional[List[str]] = Field(default_factory=list)
    estimated_points: Optional[int] = None
    story_id: Optional[str] = None

    @field_validator("dependencies", mode="before")
    @classmethod
    def ensure_dependencies_list(cls, v):
        if v is None:
            return []
        return v

    @field_validator("acceptance_criteria")
    @classmethod
    def criteria_not_empty(cls, v):
        if not v or all(not c.strip() for c in v):
            raise ValueError("At least one non‑empty acceptance criterion required")
        return v


class QualityReport(BaseModel):
    story_id: Optional[str] = None
    passes_invest: bool
    invest_details: dict
    issues: List[str]
    suggestions: List[str]
    improved_story: Optional[UserStory] = None
    quality_score: float


class ValidateGherkinOutput(BaseModel):
    valid: bool
    errors: List[str]


class WriteFeatureOutput(BaseModel):
    path: str
    bytes_written: int
