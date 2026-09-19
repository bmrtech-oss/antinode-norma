"""Plugin manifest model for Antinode Norma Platform extension plugins."""

from pathlib import Path
from typing import List, Optional, Union
import yaml
from pydantic import BaseModel, Field


class PluginManifest(BaseModel):
    name: str
    version: str = "0.1.0"
    author: Optional[str] = None
    description: Optional[str] = None
    entry_point: Optional[str] = None
    permissions: List[str] = Field(default_factory=list)
    hooks: List[str] = Field(default_factory=list)

    @classmethod
    def from_yaml(cls, path_or_yaml: Union[str, Path]) -> "PluginManifest":
        """Loads and parses a PluginManifest from a YAML file or string."""
        path = None
        if isinstance(path_or_yaml, (str, Path)):
            try:
                candidate = Path(path_or_yaml)
                if candidate.exists() and candidate.is_file():
                    path = candidate
            except OSError:
                path = None

        if path:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        else:
            data = yaml.safe_load(str(path_or_yaml))
        return cls(**(data or {}))
