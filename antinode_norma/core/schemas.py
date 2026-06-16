from pydantic import BaseModel, Field, validator
from typing import List, Optional
from enum import Enum


class UserStory(BaseModel):
    raw_text: str = ""
    role: str
    action: str
    benefit: str
    acceptance_criteria: List[str] = Field(min_items=1)
    dependencies: Optional[List[str]] = Field(default_factory=list)
    estimated_points: Optional[int] = None
    story_id: Optional[str] = None

    @validator("dependencies", pre=True, always=True)
    def ensure_dependencies_list(cls, v):
        if v is None:
            return []
        return v

    @validator("acceptance_criteria")
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
