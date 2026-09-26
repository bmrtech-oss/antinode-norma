from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from pydantic import BaseModel, Field

from antinode_aegis.config import AegisConfig
from antinode_norma.core.features import DEFAULT_FEATURE_FLAGS


class GateConfig(BaseModel):
    hard_pass_required: bool = True
    min_soft_score: float = 0.85
    min_sem_score: float = 0.85
    declarative_threshold: float = 0.90
    reuse_threshold: float = 0.90
    outline_threshold: float = 1.00
    state_threshold: float = 1.00


class CacheConfig(BaseModel):
    enabled: bool = True
    exact: bool = False
    semantic: bool = False
    cache_path: Path = Path("build/llm_cache.json")
    ttl_seconds: int = 86400


class GovernanceConfig(BaseModel):
    audit_enabled: bool = False
    approval_required: bool = False
    audit_log_path: Path = Path("build/audit_trail.jsonl")


class DeliveryConfig(BaseModel):
    testrail_url: Optional[str] = None
    testrail_user: Optional[str] = None
    testrail_project_id: Optional[str] = None
    xray_base_url: Optional[str] = None
    xray_project_key: Optional[str] = None


class HybridConfig(BaseModel):
    discovery_enabled: bool = False
    review_enabled: bool = False


class NormaConfig(BaseModel):
    aegis: AegisConfig = Field(default_factory=AegisConfig)
    gates: GateConfig = Field(default_factory=GateConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    governance: GovernanceConfig = Field(default_factory=GovernanceConfig)
    delivery: DeliveryConfig = Field(default_factory=DeliveryConfig)
    hybrid: HybridConfig = Field(default_factory=HybridConfig)
    features: Dict[str, bool] = Field(default_factory=lambda: dict(DEFAULT_FEATURE_FLAGS))


def load_config(path: Optional[Path] = None) -> NormaConfig:
    config_path = path or Path("norma.config.yml")
    config_dict: Dict[str, Any] = {}

    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if isinstance(data, dict):
                    config_dict = data
        except Exception:
            pass

    # Merge features if present in YAML or defaults
    yaml_features = config_dict.get("features", {})
    merged_features = dict(DEFAULT_FEATURE_FLAGS)
    if isinstance(yaml_features, dict):
        merged_features.update(yaml_features)
    config_dict["features"] = merged_features

    return NormaConfig(**config_dict)
