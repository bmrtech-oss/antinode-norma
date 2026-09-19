"""Unit tests for Phase 11 Task P11-T01: Plugin Manifest and Registry."""

from antinode_norma.ecosystem import PluginManifest, PluginRegistry


def test_plugin_manifest_from_dict():
    manifest = PluginManifest(
        name="jira-enhancer",
        version="1.2.0",
        author="QA Team",
        description="Enhances Jira integration",
        entry_point="jira_enhancer.plugin:entry",
        permissions=["read:features", "write:gates"],
        hooks=["post_generate", "pre_validate"],
    )

    assert manifest.name == "jira-enhancer"
    assert manifest.version == "1.2.0"
    assert manifest.permissions == ["read:features", "write:gates"]
    assert manifest.hooks == ["post_generate", "pre_validate"]


def test_plugin_manifest_from_yaml(tmp_path):
    yaml_content = """
name: slack-notifier
version: 2.0.0
author: Ops Team
permissions:
  - network:external
hooks:
  - on_approval
"""
    yaml_file = tmp_path / "plugin.yaml"
    yaml_file.write_text(yaml_content, encoding="utf-8")

    manifest = PluginManifest.from_yaml(yaml_file)
    assert manifest.name == "slack-notifier"
    assert manifest.version == "2.0.0"
    assert manifest.permissions == ["network:external"]
    assert manifest.hooks == ["on_approval"]


def test_plugin_registry_operations():
    registry = PluginRegistry()

    p1 = PluginManifest(
        name="plugin-a",
        permissions=["read:features"],
    )
    p2 = PluginManifest(
        name="plugin-b",
        permissions=["write:delivery"],
    )

    registry.register(p1, enabled=True)
    registry.register(p2, enabled=False)

    assert registry.is_enabled("plugin-a") is True
    assert registry.is_enabled("plugin-b") is False

    assert len(registry.list_plugins()) == 2
    assert len(registry.list_plugins(enabled_only=True)) == 1

    assert registry.has_permission("plugin-a", "read:features") is True
    assert registry.has_permission("plugin-a", "write:delivery") is False
    assert registry.has_permission("plugin-b", "write:delivery") is False

    registry.set_enabled("plugin-b", True)
    assert registry.has_permission("plugin-b", "write:delivery") is True

    registry.unregister("plugin-a")
    assert registry.get_plugin("plugin-a") is None
    assert len(registry.list_plugins()) == 1
