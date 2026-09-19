"""Plugin lifecycle manager for loading, initializing, and unloading extension plugins."""

import logging
from typing import Dict, Optional, Callable
from antinode_norma.ecosystem.manifest import PluginManifest
from antinode_norma.ecosystem.registry import PluginRegistry

logger = logging.getLogger(__name__)


class PluginLifecycleManager:
    def __init__(self, registry: PluginRegistry) -> None:
        self.registry = registry
        self._on_load_callbacks: Dict[str, Callable[[], None]] = {}
        self._on_unload_callbacks: Dict[str, Callable[[], None]] = {}

    def load_plugin(
        self,
        manifest: PluginManifest,
        on_load: Optional[Callable[[], None]] = None,
        on_unload: Optional[Callable[[], None]] = None,
        enabled: bool = True,
    ) -> bool:
        """Loads and registers a plugin into the platform."""
        try:
            self.registry.register(manifest, enabled=enabled)
            if on_load:
                self._on_load_callbacks[manifest.name] = on_load
                if enabled:
                    on_load()

            if on_unload:
                self._on_unload_callbacks[manifest.name] = on_unload

            logger.info(f"Loaded plugin '{manifest.name}' (v{manifest.version}).")
            return True
        except Exception as e:
            logger.error(f"Failed to load plugin '{manifest.name}': {e}")
            return False

    def unload_plugin(self, plugin_name: str) -> bool:
        """Unloads and unregisters a plugin from the platform."""
        try:
            if plugin_name in self._on_unload_callbacks:
                unload_cb = self._on_unload_callbacks.pop(plugin_name)
                unload_cb()

            self._on_load_callbacks.pop(plugin_name, None)
            self.registry.unregister(plugin_name)
            logger.info(f"Unloaded plugin '{plugin_name}'.")
            return True
        except Exception as e:
            logger.error(f"Failed to unload plugin '{plugin_name}': {e}")
            return False
