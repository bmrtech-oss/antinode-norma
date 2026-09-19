"""Plugin hook runner for safely executing extension plugin hooks."""

import logging
from typing import Any, Callable, Dict, List, Optional
from antinode_norma.ecosystem.registry import PluginRegistry

logger = logging.getLogger(__name__)


class PluginHookRunner:
    def __init__(self, registry: PluginRegistry) -> None:
        self.registry = registry
        self._hooks: Dict[str, List[Dict[str, Any]]] = {}

    def register_hook(
        self,
        hook_name: str,
        plugin_name: str,
        callback: Callable[..., Any],
        required_permission: Optional[str] = None,
    ) -> None:
        """Registers a callback for a named hook associated with a plugin."""
        if hook_name not in self._hooks:
            self._hooks[hook_name] = []

        self._hooks[hook_name].append(
            {
                "plugin_name": plugin_name,
                "callback": callback,
                "required_permission": required_permission,
            }
        )

    def trigger_hook(self, hook_name: str, *args: Any, **kwargs: Any) -> List[Any]:
        """Triggers all enabled handlers for a named hook, enforcing permissions and non-fatal error handling."""
        results: List[Any] = []
        handlers = self._hooks.get(hook_name, [])

        for item in handlers:
            plugin_name = item["plugin_name"]
            callback = item["callback"]
            req_perm = item["required_permission"]

            if not self.registry.is_enabled(plugin_name):
                continue

            if req_perm and not self.registry.has_permission(plugin_name, req_perm):
                logger.warning(
                    f"Plugin '{plugin_name}' skipped for hook '{hook_name}': missing permission '{req_perm}'."
                )
                continue

            try:
                res = callback(*args, **kwargs)
                results.append(res)
            except Exception as e:
                logger.error(f"Error executing hook '{hook_name}' in plugin '{plugin_name}': {e}")
                # Hook failures logged, non-fatal per ADR-001 Section 13

        return results
