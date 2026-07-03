"""Unit tests for ABTestTracker (Phase 1.3d)."""

import pytest
from antinode_norma.codegen.engine.ab_test_tracker import ABTestTracker, ABTestConfig


class TestABTestTracker:
    """Test A/B testing functionality."""

    def test_ab_test_config_valid(self):
        """Test creating valid ABTestConfig."""
        config = ABTestConfig(version_a="v1", version_b="v2", split_ratio=0.5)

        assert config.version_a == "v1"
        assert config.version_b == "v2"
        assert config.split_ratio == 0.5

    def test_ab_test_config_invalid_ratio(self):
        """Test invalid split_ratio raises error."""
        with pytest.raises(ValueError):
            ABTestConfig(version_a="v1", version_b="v2", split_ratio=1.5)

    def test_ab_test_deterministic_assignment(self):
        """Test that same step ID always gets same version."""
        tracker = ABTestTracker()
        config = ABTestConfig(version_a="v1", version_b="v2", split_ratio=0.5)

        # Assign same step multiple times
        assignment1 = tracker.assign_version("step_123", config)
        assignment2 = tracker.assign_version("step_123", config)
        assignment3 = tracker.assign_version("step_123", config)

        # Should always be the same
        assert assignment1 == assignment2 == assignment3

    def test_ab_test_split_ratio_respected(self):
        """Test that split ratio is approximately respected across many steps."""
        tracker = ABTestTracker()
        config = ABTestConfig(version_a="v1", version_b="v2", split_ratio=0.6)

        # Assign many steps
        assignments = {}
        for i in range(100):
            step_id = f"step_{i}"
            version = tracker.assign_version(step_id, config)
            assignments[version] = assignments.get(version, 0) + 1

        # Check split ratio is approximately correct (allow 10% margin)
        v1_ratio = assignments.get("v1", 0) / 100
        assert 0.5 <= v1_ratio <= 0.7  # Should be around 0.6

    def test_record_result_per_version(self):
        """Test recording results per version."""
        tracker = ABTestTracker()

        # Record v1 results
        tracker.record_result("step_1", "v1", confidence=0.9, success=True)
        tracker.record_result("step_2", "v1", confidence=0.8, success=False)

        # Record v2 results
        tracker.record_result("step_3", "v2", confidence=0.95, success=True)

        metrics_v1 = tracker.get_metrics("v1")
        metrics_v2 = tracker.get_metrics("v2")

        assert metrics_v1["sample_size"] == 2
        assert metrics_v1["successful_steps"] == 1
        assert metrics_v1["failed_steps"] == 1

        assert metrics_v2["sample_size"] == 1
        assert metrics_v2["successful_steps"] == 1

    def test_metrics_calculation(self):
        """Test metrics calculations."""
        tracker = ABTestTracker()

        # Record 3 successes and 1 failure (75% success rate)
        tracker.record_result("step_1", "v1", confidence=0.9, success=True)
        tracker.record_result("step_2", "v1", confidence=0.85, success=True)
        tracker.record_result("step_3", "v1", confidence=0.88, success=True)
        tracker.record_result("step_4", "v1", confidence=0.92, success=False)

        metrics = tracker.get_metrics("v1")

        assert metrics["sample_size"] == 4
        assert metrics["successful_steps"] == 3
        assert metrics["failed_steps"] == 1
        assert metrics["success_rate"] == 0.75
        assert 0.88 <= metrics["average_confidence"] <= 0.89  # (0.9+0.85+0.88+0.92)/4

    def test_record_skipped(self):
        """Test recording skipped results."""
        tracker = ABTestTracker()

        tracker.record_result("step_1", "v1", confidence=0.8, success=True)
        tracker.record_skipped("step_2", "v1", confidence=0.7)

        metrics = tracker.get_metrics("v1")

        assert metrics["sample_size"] == 2
        assert metrics["successful_steps"] == 1
        assert metrics["skipped_steps"] == 1

    def test_get_winner_v1_better(self):
        """Test determining winner when v1 is better."""
        tracker = ABTestTracker()
        config = ABTestConfig(version_a="v1", version_b="v2", split_ratio=0.5)

        # v1: 8 successes out of 10
        for i in range(8):
            tracker.record_result(f"v1_step_{i}", "v1", confidence=0.9, success=True)
        for i in range(2):
            tracker.record_result(f"v1_step_fail_{i}", "v1", confidence=0.8, success=False)

        # v2: 5 successes out of 10
        for i in range(5):
            tracker.record_result(f"v2_step_{i}", "v2", confidence=0.9, success=True)
        for i in range(5):
            tracker.record_result(f"v2_step_fail_{i}", "v2", confidence=0.8, success=False)

        winner = tracker.get_winner(config)
        assert winner == "v1"

    def test_get_winner_v2_better(self):
        """Test determining winner when v2 is better."""
        tracker = ABTestTracker()
        config = ABTestConfig(version_a="v1", version_b="v2", split_ratio=0.5)

        # v1: 5 successes out of 10
        for i in range(5):
            tracker.record_result(f"v1_step_{i}", "v1", confidence=0.9, success=True)
        for i in range(5):
            tracker.record_result(f"v1_step_fail_{i}", "v1", confidence=0.8, success=False)

        # v2: 9 successes out of 10
        for i in range(9):
            tracker.record_result(f"v2_step_{i}", "v2", confidence=0.9, success=True)
        for i in range(1):
            tracker.record_result(f"v2_step_fail_{i}", "v2", confidence=0.8, success=False)

        winner = tracker.get_winner(config)
        assert winner == "v2"

    def test_get_winner_insufficient_samples(self):
        """Test that get_winner returns None if not enough samples."""
        tracker = ABTestTracker()
        config = ABTestConfig(version_a="v1", version_b="v2", split_ratio=0.5)

        # Only 5 samples each (minimum is 10)
        for i in range(5):
            tracker.record_result(f"v1_step_{i}", "v1", confidence=0.9, success=True)
            tracker.record_result(f"v2_step_{i}", "v2", confidence=0.9, success=True)

        winner = tracker.get_winner(config)
        assert winner is None

    def test_clear_all(self):
        """Test clearing all tracking data."""
        tracker = ABTestTracker()

        tracker.record_result("step_1", "v1", confidence=0.9, success=True)
        tracker.assign_version("step_123", ABTestConfig(version_a="v1", version_b="v2"))

        assert len(tracker.metrics) > 0
        assert len(tracker.assignments) > 0

        tracker.clear_all()

        assert len(tracker.metrics) == 0
        assert len(tracker.assignments) == 0

    def test_get_all_metrics(self):
        """Test retrieving all metrics at once."""
        tracker = ABTestTracker()

        tracker.record_result("step_1", "v1", confidence=0.9, success=True)
        tracker.record_result("step_2", "v1", confidence=0.8, success=False)
        tracker.record_result("step_3", "v2", confidence=0.95, success=True)

        all_metrics = tracker.get_all_metrics()

        assert "v1" in all_metrics
        assert "v2" in all_metrics
        assert all_metrics["v1"]["sample_size"] == 2
        assert all_metrics["v2"]["sample_size"] == 1
