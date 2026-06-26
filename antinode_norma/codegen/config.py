"""
Configuration for the code generation module.

Settings are loaded from:
1. Defaults (hard‑coded in dataclass)
2. Optional YAML file (codegen.yaml or codegen.yml) – auto‑discovered if present
3. Environment variables (prefix CODEGEN_) – these override everything
4. .env file (if python-dotenv is installed)
"""

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any

from .engine.quality import QualityConfig


@dataclass
class CodegenConfig:
    """Holds all configuration for the code generator."""

    # Core settings
    default_framework: str = "playwright"
    feature_dir: Path = Path("features")
    output_dir: Path = Path("generated_tests")
    base_url: Optional[str] = None
    framework_output_map: Dict[str, str] = field(
        default_factory=lambda: {
            "playwright": "playwright",
            "cypress": "cypress",
            "selenium": "selenium",
        }
    )
    parser_options: Dict[str, Any] = field(default_factory=dict)
    emitter_options: Dict[str, Any] = field(default_factory=dict)
    verbose: bool = False
    dry_run: bool = False

    # Quality enhancements (nested)
    quality: QualityConfig = field(default_factory=QualityConfig)

    def __post_init__(self):
        # Ensure paths are Path objects
        self.feature_dir = Path(self.feature_dir)
        self.output_dir = Path(self.output_dir)

        # Convert quality dict to QualityConfig, filtering unknown keys
        if isinstance(self.quality, dict):
            # Get valid field names from QualityConfig
            valid_keys = {f.name for f in QualityConfig.__dataclass_fields__.values()}
            filtered = {k: v for k, v in self.quality.items() if k in valid_keys}
            self.quality = QualityConfig(**filtered)

    def get_output_dir(self, framework: Optional[str] = None) -> Path:
        """Return the output directory for a given framework."""
        fw = framework or self.default_framework
        sub = self.framework_output_map.get(fw, fw)
        return self.output_dir / sub


def _load_dotenv():
    """Load .env file using python-dotenv if available."""
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass


def _set_nested(dic: dict, key: str, value: Any):
    """Set a nested dictionary value using dot notation."""
    parts = key.split(".")
    for part in parts[:-1]:
        dic = dic.setdefault(part, {})
    dic[parts[-1]] = value


def _parse_env_value(value: str) -> Any:
    normalized = value.strip()
    lower = normalized.lower()
    if lower in {"true", "1", "yes", "on"}:
        return True
    if lower in {"false", "0", "no", "off"}:
        return False
    if lower == "null":
        return None
    if re.fullmatch(r"-?\d+", normalized):
        return int(normalized)
    if re.fullmatch(r"-?\d+\.\d+", normalized):
        try:
            return float(normalized)
        except ValueError:
            pass
    if normalized.startswith("[") or normalized.startswith("{"):
        try:
            return json.loads(normalized)
        except json.JSONDecodeError:
            pass
    return value


def _clean_config_dict(config_dict: dict) -> dict:
    """
    Clean and normalize configuration dictionary.
    Handles aliases and removes invalid keys.
    """
    # Alias mapping: old_key -> new_key
    alias_map = {
        "default": "default_framework",
        "output": "output_dir",
    }

    for old_key, new_key in alias_map.items():
        if old_key in config_dict:
            if new_key not in config_dict:
                config_dict[new_key] = config_dict.pop(old_key)
            else:
                config_dict.pop(old_key)

    # Remove any keys that start with underscore
    for key in list(config_dict.keys()):
        if key.startswith("_"):
            config_dict.pop(key)

    return config_dict


def load_config(config_file: Optional[Path] = None, auto_discover: bool = True) -> CodegenConfig:
    """
    Load configuration from environment variables and optionally a YAML file.
    """
    _load_dotenv()

    config_dict = {}

    # Determine config file
    if config_file is None and auto_discover:
        env_config = os.environ.get("CODEGEN_CONFIG_FILE")
        if env_config:
            config_file = Path(env_config)
        else:
            for ext in [".yaml", ".yml"]:
                default_path = Path("codegen" + ext)
                if default_path.exists():
                    config_file = default_path
                    break

    # Load YAML
    if config_file and config_file.exists():
        try:
            import yaml

            with open(config_file, "r", encoding="utf-8") as f:
                file_config = yaml.safe_load(f)
                if file_config:
                    config_dict.update(file_config)
        except Exception:
            pass

    config_dict = _clean_config_dict(config_dict)

    # Environment variables (highest priority)
    env_prefix = "CODEGEN_"
    for key, value in os.environ.items():
        if key.startswith(env_prefix):
            env_key = key[len(env_prefix) :].lower()
            if env_key.startswith("quality_"):
                env_key = f"quality.{env_key[len('quality_'):]}"
            elif env_key.startswith("parser_options_"):
                env_key = f"parser_options.{env_key[len('parser_options_'):]}"
            elif env_key.startswith("emitter_options_"):
                env_key = f"emitter_options.{env_key[len('emitter_options_'):]}"
            elif "__" in env_key:
                env_key = env_key.replace("__", ".")
            _set_nested(config_dict, env_key, _parse_env_value(value))

    config_dict = _clean_config_dict(config_dict)

    # Convert paths
    if "feature_dir" in config_dict:
        config_dict["feature_dir"] = Path(config_dict["feature_dir"])
    if "output_dir" in config_dict:
        config_dict["output_dir"] = Path(config_dict["output_dir"])

    return CodegenConfig(**config_dict)


# Global singleton config
_default_config = load_config()


def get_config() -> CodegenConfig:
    """Return the global configuration instance."""
    return _default_config


def set_config(config: CodegenConfig) -> None:
    """Replace the global configuration."""
    global _default_config
    _default_config = config
