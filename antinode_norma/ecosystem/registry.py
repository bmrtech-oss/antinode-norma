"""Plugin registry for managing extension plugin registration and permissions."""

from typing import Dict, List, Optional
from antinode_norma.ecosystem.manifest import PluginManifest


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: Dict[str, PluginManifest] = {}
        self._enabled: Dict[str, bool] = {}

    def register(self, manifest: PluginManifest, enabled: bool = True) -> None:
        """Registers a plugin manifest into the registry."""
        self._plugins[manifest.name] = manifest
        self._enabled[manifest.name] = enabled

    def unregister(self, plugin_name: str) -> None:
        """Unregisters a plugin by name."""
        self._plugins.pop(plugin_name, None)
        self._enabled.pop(plugin_name, None)

    def is_enabled(self, plugin_name: str) -> bool:
        """Checks if a plugin is currently registered and enabled."""
        return self._enabled.get(plugin_name, False)

    def set_enabled(self, plugin_name: str, enabled: bool) -> None:
        """Enables or disables a registered plugin."""
        if plugin_name in self._plugins:
            self._enabled[plugin_name] = enabled

    def get_plugin(self, plugin_name: str) -> Optional[PluginManifest]:
        """Retrieves plugin manifest by name if registered."""
        return self._plugins.get(plugin_name)

    def list_plugins(self, enabled_only: bool = False) -> List[PluginManifest]:
        """Lists registered plugins, optionally filtering by enabled status."""
        if enabled_only:
            return [p for name, p in self._plugins.items() if self._enabled.get(name, False)]
        return list(self._plugins.values())

    def has_permission(self, plugin_name: str, permission: str) -> bool:
        """Checks if an enabled plugin holds the requested permission."""
        if not self.is_enabled(plugin_name):
            return False
        plugin = self.get_plugin(plugin_name)
        return bool(plugin and permission in plugin.permissions)
