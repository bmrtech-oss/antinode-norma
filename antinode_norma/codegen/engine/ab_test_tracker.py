"""A/B testing and version tracking for prompt templates."""

from dataclasses import dataclass
from typing import Dict, Optional
import hashlib


@dataclass
class ABTestConfig:
    """Configuration for A/B testing between two prompt versions."""

    version_a: str  # e.g., "v1"
    version_b: str  # e.g., "v2"
    split_ratio: float = 0.5  # Proportion assigned to version_a (0.0-1.0)

    def __post_init__(self):
        """Validate config after initialization."""
        if not 0.0 <= self.split_ratio <= 1.0:
            raise ValueError("split_ratio must be between 0.0 and 1.0")


@dataclass
class VersionMetrics:
    """Metrics for a specific prompt version."""

    version: str
    total_steps: int = 0
    successful_steps: int = 0
    failed_steps: int = 0
    skipped_steps: int = 0
    total_confidence: float = 0.0

    @property
    def success_rate(self) -> float:
        """Calculate success rate (0.0-1.0)."""
        if self.total_steps == 0:
            return 0.0
        return self.successful_steps / self.total_steps

    @property
    def average_confidence(self) -> float:
        """Calculate average confidence score."""
        if self.total_steps == 0:
            return 0.0
        return self.total_confidence / self.total_steps


class ABTestTracker:
    """Track A/B testing results for prompt versions."""

    def __init__(self):
        """Initialize A/B test tracker."""
        self.metrics: Dict[str, VersionMetrics] = {}
        self.assignments: Dict[str, str] = {}  # step_id -> version assignment

    def assign_version(self, step_id: str, config: ABTestConfig) -> str:
        """
        Deterministically assign step to version A or B.

        Args:
            step_id: Unique identifier for the step
            config: ABTestConfig with versions and split ratio

        Returns:
            Assigned version ("v1" or "v2", etc.)
        """
        # Return cached assignment if exists
        if step_id in self.assignments:
            return self.assignments[step_id]

        # Deterministic assignment: hash step_id to decide
        # Use step_id hash to ensure same step always gets same version
        hash_value = int(
            hashlib.md5(step_id.encode()).hexdigest(), 16
        )  # Convert hex to int
        ratio_value = hash_value % 100  # Map to 0-99

        # Assign based on split_ratio
        threshold = int(config.split_ratio * 100)
        assigned = config.version_a if ratio_value < threshold else config.version_b

        self.assignments[step_id] = assigned
        return assigned

    def record_result(
        self, step_id: str, version: str, confidence: float, success: bool
    ) -> None:
        """
        Log result for a specific version.

        Args:
            step_id: Unique identifier for the step
            version: Version that was used
            confidence: Confidence score (0.0-1.0)
            success: Whether the test passed
        """
        if version not in self.metrics:
            self.metrics[version] = VersionMetrics(version=version)

        metrics = self.metrics[version]
        metrics.total_steps += 1
        metrics.total_confidence += confidence

        if success:
            metrics.successful_steps += 1
        else:
            metrics.failed_steps += 1

    def record_skipped(self, step_id: str, version: str, confidence: float) -> None:
        """Log skipped result for a version."""
        if version not in self.metrics:
            self.metrics[version] = VersionMetrics(version=version)

        metrics = self.metrics[version]
        metrics.total_steps += 1
        metrics.total_confidence += confidence
        metrics.skipped_steps += 1

    def get_metrics(self, version: str) -> Optional[Dict[str, float]]:
        """
        Return metrics for a version.

        Args:
            version: Version to get metrics for

        Returns:
            Dict with success_rate, avg_confidence, sample_size, or None
        """
        if version not in self.metrics:
            return None

        metrics = self.metrics[version]
        return {
            "success_rate": metrics.success_rate,
            "average_confidence": metrics.average_confidence,
            "sample_size": metrics.total_steps,
            "successful_steps": metrics.successful_steps,
            "failed_steps": metrics.failed_steps,
            "skipped_steps": metrics.skipped_steps,
        }

    def get_winner(self, config: ABTestConfig) -> Optional[str]:
        """
        Determine winning version based on success rates.

        Args:
            config: ABTestConfig for reference

        Returns:
            Winning version or None if not enough data
        """
        a_metrics = self.get_metrics(config.version_a)
        b_metrics = self.get_metrics(config.version_b)

        if not a_metrics or not b_metrics:
            return None

        # Need minimum sample size (e.g., 10)
        min_samples = 10
        if (
            a_metrics["sample_size"] < min_samples
            or b_metrics["sample_size"] < min_samples
        ):
            return None

        a_rate = a_metrics["success_rate"]
        b_rate = b_metrics["success_rate"]

        if a_rate > b_rate:
            return config.version_a
        elif b_rate > a_rate:
            return config.version_b
        else:
            return None  # Tie

    def clear_all(self) -> None:
        """Clear all tracking data."""
        self.metrics.clear()
        self.assignments.clear()

    def get_all_metrics(self) -> Dict[str, Dict[str, float]]:
        """
        Get all metrics for all versions.

        Returns:
            Dict mapping version -> metrics
        """
        result = {}
        for version in self.metrics:
            result[version] = self.get_metrics(version) or {}
        return result
