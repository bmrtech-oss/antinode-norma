"""Unit tests for Phase 11 Task P11-T02: Plugin Hooks and Lifecycle."""

from antinode_norma.ecosystem import (
    PluginHookRunner,
    PluginLifecycleManager,
    PluginManifest,
    PluginRegistry,
)


def test_plugin_hook_execution_and_permissions():
    registry = PluginRegistry()
    runner = PluginHookRunner(registry)

    manifest_a = PluginManifest(name="plugin-a", permissions=["read:features"])
    manifest_b = PluginManifest(name="plugin-b", permissions=[])

    registry.register(manifest_a, enabled=True)
    registry.register(manifest_b, enabled=True)

    results_a = []
    results_b = []

    runner.register_hook(
        hook_name="on_generate",
        plugin_name="plugin-a",
        callback=lambda text: results_a.append(f"A:{text}"),
        required_permission="read:features",
    )
    runner.register_hook(
        hook_name="on_generate",
        plugin_name="plugin-b",
        callback=lambda text: results_b.append(f"B:{text}"),
        required_permission="write:gates",
    )

    runner.trigger_hook("on_generate", text="hello")

    # Plugin A has read:features so callback runs
    assert results_a == ["A:hello"]
    # Plugin B lacks write:gates permission so callback skipped
    assert results_b == []


def test_plugin_hook_non_fatal_error_handling():
    registry = PluginRegistry()
    runner = PluginHookRunner(registry)

    manifest = PluginManifest(name="faulty-plugin", permissions=[])
    registry.register(manifest, enabled=True)

    def faulty_callback():
        raise RuntimeError("Something went wrong inside plugin hook!")

    runner.register_hook(
        hook_name="on_event",
        plugin_name="faulty-plugin",
        callback=faulty_callback,
    )

    # Executing faulty hook should not raise exception (non-fatal error handling)
    res = runner.trigger_hook("on_event")
    assert res == []


def test_plugin_lifecycle_load_and_unload():
    registry = PluginRegistry()
    lifecycle = PluginLifecycleManager(registry)

    loaded_state = {"loaded": False, "unloaded": False}

    def on_load():
        loaded_state["loaded"] = True

    def on_unload():
        loaded_state["unloaded"] = True

    manifest = PluginManifest(name="lifecycle-plugin")

    success = lifecycle.load_plugin(
        manifest=manifest,
        on_load=on_load,
        on_unload=on_unload,
        enabled=True,
    )

    assert success is True
    assert registry.is_enabled("lifecycle-plugin") is True
    assert loaded_state["loaded"] is True

    unload_success = lifecycle.unload_plugin("lifecycle-plugin")
    assert unload_success is True
    assert registry.get_plugin("lifecycle-plugin") is None
    assert loaded_state["unloaded"] is True
