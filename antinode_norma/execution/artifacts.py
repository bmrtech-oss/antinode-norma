import shutil
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field


class ArtifactType(str, Enum):
    SCREENSHOT = "SCREENSHOT"
    VIDEO = "VIDEO"
    TRACE = "TRACE"
    LOG = "LOG"


class Artifact(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    execution_id: str
    artifact_type: ArtifactType
    file_path: str
    content_type: str = "application/octet-stream"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    size_bytes: int = 0


class ArtifactManager:
    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or Path("build/artifacts")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.artifacts: List[Artifact] = []

    def save_artifact(
        self,
        execution_id: str,
        artifact_type: ArtifactType,
        source_data: bytes,
        filename: str,
        content_type: str = "application/octet-stream",
    ) -> Artifact:
        exec_dir = self.output_dir / execution_id
        exec_dir.mkdir(parents=True, exist_ok=True)
        target_path = exec_dir / filename

        with open(target_path, "wb") as f:
            f.write(source_data)

        artifact = Artifact(
            execution_id=execution_id,
            artifact_type=artifact_type,
            file_path=str(target_path),
            content_type=content_type,
            size_bytes=len(source_data),
        )
        self.artifacts.append(artifact)
        return artifact

    def get_artifacts(
        self,
        execution_id: Optional[str] = None,
        artifact_type: Optional[ArtifactType] = None,
    ) -> List[Artifact]:
        res = self.artifacts
        if execution_id:
            res = [a for a in res if a.execution_id == execution_id]
        if artifact_type:
            res = [a for a in res if a.artifact_type == artifact_type]
        return res

    def clear_artifacts(self, execution_id: Optional[str] = None) -> None:
        if execution_id:
            exec_dir = self.output_dir / execution_id
            if exec_dir.exists():
                shutil.rmtree(exec_dir)
            self.artifacts = [a for a in self.artifacts if a.execution_id != execution_id]
        else:
            if self.output_dir.exists():
                shutil.rmtree(self.output_dir)
                self.output_dir.mkdir(parents=True, exist_ok=True)
            self.artifacts = []
