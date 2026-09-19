"""Unit tests for Phase 11 Task P11-T03: Plugin SDK Package."""

from typing import Dict, Any
from antinode_norma.ecosystem import (
    DeliveryAdapterPlugin,
    FeatureGeneratorPlugin,
    PluginManifest,
    QualityGatePlugin,
)


class CustomGeneratorPlugin(FeatureGeneratorPlugin):
    def generate_feature(self, source_text: str) -> str:
        return f"Feature: Generated from {source_text}"


class CustomGatePlugin(QualityGatePlugin):
    def evaluate_gate(self, gherkin_text: str) -> Dict[str, Any]:
        return {"passed": "Feature:" in gherkin_text, "score": 1.0}


class CustomDeliveryPlugin(DeliveryAdapterPlugin):
    def publish_feature(self, feature_id: str, content: str) -> bool:
        return len(feature_id) > 0 and len(content) > 0


def test_base_plugin_capabilities():
    manifest = PluginManifest(
        name="test-plugin",
        version="1.0.0",
        permissions=["read:features"],
        hooks=["on_generate"],
    )
    plugin = CustomGeneratorPlugin(manifest)

    capabilities = plugin.get_capabilities()
    assert capabilities["name"] == "test-plugin"
    assert capabilities["version"] == "1.0.0"
    assert capabilities["permissions"] == ["read:features"]
    assert capabilities["hooks"] == ["on_generate"]


def test_custom_feature_generator_plugin():
    manifest = PluginManifest(name="gen-plugin")
    plugin = CustomGeneratorPlugin(manifest)

    feature_output = plugin.generate_feature("User Login Story")
    assert feature_output == "Feature: Generated from User Login Story"


def test_custom_quality_gate_plugin():
    manifest = PluginManifest(name="gate-plugin")
    plugin = CustomGatePlugin(manifest)

    res = plugin.evaluate_gate("Feature: Sample Checkout")
    assert res["passed"] is True
    assert res["score"] == 1.0


def test_custom_delivery_adapter_plugin():
    manifest = PluginManifest(name="delivery-plugin")
    plugin = CustomDeliveryPlugin(manifest)

    published = plugin.publish_feature("FEAT-101", "Feature: Login")
    assert published is True
