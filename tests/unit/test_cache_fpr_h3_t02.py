"""Unit tests for Phase H3 Task H3-T02: Cache False-Positive Rate (FPR) Gate."""

import tempfile
import unittest
from pathlib import Path

from antinode_norma.cache.semantic import SemanticPromptCache, _jaccard_similarity, _tokenize
from tests.fixtures.cache_golden_pairs import NEAR_MISS_GOLDEN_PAIRS


class TestCacheFPRH3T02(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.cache_path = Path(self.temp_dir.name) / "semantic_cache.json"
        self.cache = SemanticPromptCache(cache_path=self.cache_path, similarity_threshold=0.85)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_cache_fpr_calculation_and_auto_disable(self):
        self.assertEqual(self.cache.cache_false_positive_rate, 0.0)

        # Record 100 cache hits, 3 of which fail soft quality gates (FPR = 3% > 2% gate)
        for _ in range(97):
            self.cache.record_soft_gate_outcome(hit_failed_soft_gates=False)
        for _ in range(3):
            self.cache.record_soft_gate_outcome(hit_failed_soft_gates=True)

        self.assertAlmostEqual(self.cache.cache_false_positive_rate, 0.03)

        # Cache hit attempt when FPR > 2% must return None (auto-disabled)
        self.cache.set("User login feature", "Feature: Login")
        hit = self.cache.get("User login feature")
        self.assertIsNone(hit)

    def test_golden_near_miss_pairs_negative_caching(self):
        # Assert that all 20 near-miss golden pairs fall below similarity threshold (0.85)
        for p1, p2 in NEAR_MISS_GOLDEN_PAIRS:
            score = _jaccard_similarity(_tokenize(p1), _tokenize(p2))
            self.assertLess(score, 0.85, f"Near-miss pair '{p1}' vs '{p2}' unexpectedly matched with score {score}")

            # Store p1 in cache
            self.cache.set(p1, "Feature: Generated p1")

            # p2 lookup must return None
            match = self.cache.get(p2)
            self.assertIsNone(match, f"Near-miss prompt '{p2}' unexpectedly hit cache for '{p1}'")


if __name__ == "__main__":
    unittest.main()
