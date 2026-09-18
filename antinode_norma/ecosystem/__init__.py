"""Ecosystem package for Antinode Norma plugins and extensions."""

from antinode_norma.ecosystem.manifest import PluginManifest
from antinode_norma.ecosystem.registry import PluginRegistry
from antinode_norma.ecosystem.hooks import PluginHookRunner
from antinode_norma.ecosystem.lifecycle import PluginLifecycleManager

__all__ = [
    "PluginManifest",
    "PluginRegistry",
    "PluginHookRunner",
    "PluginLifecycleManager",
]
