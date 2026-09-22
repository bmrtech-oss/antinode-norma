"""User and Role models for Antinode Norma Platform SSO & RBAC."""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class Role(str, Enum):
    ADMIN = "admin"
    REVIEWER = "reviewer"
    GENERATOR = "generator"
    VIEWER = "viewer"


class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: str
    roles: List[Role] = Field(default_factory=lambda: [Role.VIEWER])
    is_active: bool = True
    tenant_id: Optional[str] = None
    display_name: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
