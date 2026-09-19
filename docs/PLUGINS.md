# Antinode Norma BDD Platform - Plugin Ecosystem & Collaboration Documentation

This document describes the plugin ecosystem model, SDK interfaces, hook execution lifecycle, collaboration tools (comments & mentions), multi-channel notifications, and analytics APIs for the Antinode Norma Platform.

---

## 1. Plugin Manifest Schema (`plugin.yaml`)

Plugins declare capabilities, required permissions, and registered hooks using `plugin.yaml`:

```yaml
name: slack-approval-notifier
version: 1.0.0
author: QA Automation Team
description: Dispatches Slack alerts when features require approval.
entry_point: slack_approval_notifier.plugin:entry
permissions:
  - network:external
hooks:
  - on_approval_requested
```

### Python Manifest Model

```python
from antinode_norma.ecosystem import PluginManifest

manifest = PluginManifest.from_yaml("plugin.yaml")
```

---

## 2. Plugin Registry & Lifecycle Management

The `PluginRegistry` maintains registered extension plugins, status (`enabled`/`disabled`), and permission authorization:

```python
from antinode_norma.ecosystem import PluginRegistry, PluginLifecycleManager, PluginManifest

registry = PluginRegistry()
lifecycle = PluginLifecycleManager(registry)

manifest = PluginManifest(name="my-plugin", permissions=["read:features"])
lifecycle.load_plugin(manifest, enabled=True)
```

---

## 3. Plugin Hook Execution

`PluginHookRunner` executes registered plugin callbacks with non-fatal exception handling and permission checks:

```python
from antinode_norma.ecosystem import PluginHookRunner

runner = PluginHookRunner(registry)
runner.register_hook(
    hook_name="on_feature_generate",
    plugin_name="my-plugin",
    callback=lambda text: print(f"Generated: {text}"),
    required_permission="read:features",
)

results = runner.trigger_hook("on_feature_generate", text="Feature: Checkout")
```

---

## 4. Plugin SDK Base Classes

Plugin developers inherit from standard abstract base classes in `antinode_norma.ecosystem`:

- `BasePlugin`: Fundamental plugin base class (`on_load()`, `on_unload()`, `get_capabilities()`).
- `FeatureGeneratorPlugin`: Custom feature generator interface (`generate_feature(source_text)`).
- `QualityGatePlugin`: Custom quality criteria validation interface (`evaluate_gate(gherkin_text)`).
- `DeliveryAdapterPlugin`: Custom delivery adapter interface (`publish_feature(feature_id, content)`).

---

## 5. Collaboration: Comments & Mentions

- Model & Store: `Comment`, `CommentStore`, `extract_mentions` in `antinode_norma.collaboration`.
- Automatic `@username` extraction parses user mentions from comment text.
- API Endpoints:
  - `GET /api/comments?feature_id=...`
  - `POST /api/comments`

---

## 6. Multi-Channel Notifications

- `NotificationManager` supports Slack, Teams, and Email dispatchers.
- Webhooks configured via `SLACK_WEBHOOK_URL` and `TEAMS_WEBHOOK_URL` with graceful unconfigured fallback.
- API Endpoint: `POST /api/notifications/send`

---

## 7. Analytics Dashboard

- `AnalyticsCollector` computes platform throughput, quality gate pass rates, approval conversion rates, audit event totals, and trend series.
- API Endpoint: `GET /api/analytics/summary`
