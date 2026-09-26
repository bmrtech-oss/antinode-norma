import shutil
import os
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
    def __init__(self, output_dir: Optional[Path] = None, database_url: Optional[str] = None):
        self.output_dir = output_dir or Path("build/artifacts")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.database_url = database_url or os.getenv("DATABASE_URL")
        self.artifacts: List[Artifact] = []
        if self.database_url:
            from antinode_norma.database import load_execution_artifacts, migrate

            migrate(self.database_url)
            self.artifacts = [
                Artifact(**record)
                for record in load_execution_artifacts(self.database_url, self._storage_root)
            ]

    @property
    def _storage_root(self) -> str:
        return str(self.output_dir.resolve())

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
        if self.database_url:
            from antinode_norma.database import save_execution_artifact

            try:
                save_execution_artifact(
                    self.database_url,
                    self._storage_root,
                    artifact.model_dump(mode="json"),
                )
            except Exception:
                target_path.unlink(missing_ok=True)
                raise
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
            if self.database_url:
                from antinode_norma.database import delete_execution_artifacts

                delete_execution_artifacts(self.database_url, self._storage_root, execution_id)
        else:
            if self.output_dir.exists():
                shutil.rmtree(self.output_dir)
                self.output_dir.mkdir(parents=True, exist_ok=True)
            self.artifacts = []
            if self.database_url:
                from antinode_norma.database import delete_execution_artifacts

                delete_execution_artifacts(self.database_url, self._storage_root)
