"""Unit tests for Phase H4 Task H4-T01: Cross-Track Regression Gate."""

import unittest
from bin.run_regression_gate import run_cross_track_regression_gate


class TestRegressionGateH4T01(unittest.TestCase):
    def test_run_cross_track_regression_gate(self):
        res = run_cross_track_regression_gate()
        self.assertTrue(res)


if __name__ == "__main__":
    unittest.main()
