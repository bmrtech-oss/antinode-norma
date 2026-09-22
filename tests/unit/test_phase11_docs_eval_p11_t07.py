"""Unit tests for Phase 11 Task P11-T07: Phase 11 Integrated Workflow Verification."""

from antinode_norma.analytics import AnalyticsCollector, AnalyticsSummary
from antinode_norma.collaboration import CommentStore, NotificationManager
from antinode_norma.ecosystem import (
    PluginHookRunner,
    PluginManifest,
    PluginRegistry,
)


def test_phase11_integrated_workflow():
    # 1. Register plugin
    registry = PluginRegistry()
    manifest = PluginManifest(name="eval-plugin", permissions=["read:features"])
    registry.register(manifest, enabled=True)

    # 2. Trigger hook
    runner = PluginHookRunner(registry)
    events = []
    runner.register_hook(
        hook_name="on_comment",
        plugin_name="eval-plugin",
        callback=lambda text: events.append(text),
        required_permission="read:features",
    )
    runner.trigger_hook("on_comment", text="Comment created")
    assert events == ["Comment created"]

    # 3. Add comment & mentions
    comment_store = CommentStore()
    c = comment_store.add_comment(
        feature_id="feat-p11",
        author_id="user_qa",
        text="Reviewing feature @dev_lead",
    )
    assert c.mentions == ["dev_lead"]

    # 4. Dispatch notification
    notif_mgr = NotificationManager()
    from antinode_norma.collaboration import Notification

    n = Notification(
        event_type="comment_added",
        title="New Comment",
        message=c.text,
        channel="email",
        recipient="dev_lead@norma.local",
    )
    res = notif_mgr.send_notification(n)
    assert res["status"] == "sent"

    # 5. Collect analytics summary
    collector = AnalyticsCollector()
    summary = collector.collect_summary(feature_count=1)
    assert isinstance(summary, AnalyticsSummary)
