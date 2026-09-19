"""Plugin SDK package providing standard extension base classes for plugin developers."""

from abc import ABC, abstractmethod
from typing import Dict, Any
from antinode_norma.ecosystem.manifest import PluginManifest


class BasePlugin(ABC):
    """Abstract base class for all Antinode Norma extension plugins."""

    def __init__(self, manifest: PluginManifest) -> None:
        self.manifest = manifest

    def on_load(self) -> None:
        """Called when plugin is initialized/loaded."""
        pass

    def on_unload(self) -> None:
        """Called when plugin is shut down/unloaded."""
        pass

    def get_capabilities(self) -> Dict[str, Any]:
        """Returns declared plugin capabilities and metadata."""
        return {
            "name": self.manifest.name,
            "version": self.manifest.version,
            "permissions": self.manifest.permissions,
            "hooks": self.manifest.hooks,
        }


class FeatureGeneratorPlugin(BasePlugin, ABC):
    """Extension interface for custom BDD feature generation plugins."""

    @abstractmethod
    def generate_feature(self, source_text: str) -> str:
        """Generates Gherkin feature text from input source text."""
        pass


class QualityGatePlugin(BasePlugin, ABC):
    """Extension interface for custom quality gate validation plugins."""

    @abstractmethod
    def evaluate_gate(self, gherkin_text: str) -> Dict[str, Any]:
        """Evaluates custom quality criteria against Gherkin feature text."""
        pass


class DeliveryAdapterPlugin(BasePlugin, ABC):
    """Extension interface for custom delivery/publishing adapter plugins."""

    @abstractmethod
    def publish_feature(self, feature_id: str, content: str) -> bool:
        """Publishes feature content to an external platform or target system."""
        pass
