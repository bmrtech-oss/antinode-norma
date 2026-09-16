import os
import yaml
from pathlib import Path
from typing import Dict, Optional

DEFAULT_FEATURE_FLAGS: Dict[str, bool] = {
    "unified_agent": False,
    "cache_exact": False,
    "cache_semantic": False,
    "governance_audit": False,
    "governance_approval": False,
    "auth_saml": False,
    "execution_cloud": False,
    "edge_discovery": False,
}


class FeatureFlagResolver:
    """Resolves feature flags using hierarchy:

    default -> norma.config.yml -> NORMA_FEATURE_<NAME> env var -> runtime overrides.
    """

    def __init__(
        self,
        config_path: Optional[Path] = None,
        runtime_overrides: Optional[Dict[str, bool]] = None,
    ):
        self.config_path = config_path or Path("norma.config.yml")
        self.runtime_overrides = runtime_overrides or {}
        self.config_flags: Dict[str, bool] = self._load_config_flags()

    def _load_config_flags(self) -> Dict[str, bool]:
        if not self.config_path.exists():
            return {}
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                return data.get("features", {})
        except Exception:
            return {}

    def is_enabled(
        self, flag_name: str, cli_override: Optional[bool] = None
    ) -> bool:
        if cli_override is not None:
            return cli_override

        if flag_name in self.runtime_overrides:
            return self.runtime_overrides[flag_name]

        env_var_name = f"NORMA_FEATURE_{flag_name.upper()}"
        if env_var_name in os.environ:
            val = os.environ[env_var_name].lower()
            return val in ("true", "1", "yes", "on")

        if flag_name in self.config_flags:
            return bool(self.config_flags[flag_name])

        return DEFAULT_FEATURE_FLAGS.get(flag_name, False)

    def get_all_flags(self) -> Dict[str, bool]:
        flags = {}
        all_keys = (
            set(DEFAULT_FEATURE_FLAGS.keys())
            | set(self.config_flags.keys())
            | set(self.runtime_overrides.keys())
        )
        for key in all_keys:
            flags[key] = self.is_enabled(key)
        return flags
