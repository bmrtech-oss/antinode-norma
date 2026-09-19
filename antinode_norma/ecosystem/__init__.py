"""Ecosystem package for Antinode Norma plugins and extensions."""

from antinode_norma.ecosystem.manifest import PluginManifest
from antinode_norma.ecosystem.registry import PluginRegistry
from antinode_norma.ecosystem.hooks import PluginHookRunner
from antinode_norma.ecosystem.lifecycle import PluginLifecycleManager
from antinode_norma.ecosystem.sdk import (
    BasePlugin,
    FeatureGeneratorPlugin,
    QualityGatePlugin,
    DeliveryAdapterPlugin,
)

__all__ = [
    "PluginManifest",
    "PluginRegistry",
    "PluginHookRunner",
    "PluginLifecycleManager",
    "BasePlugin",
    "FeatureGeneratorPlugin",
    "QualityGatePlugin",
    "DeliveryAdapterPlugin",
]
