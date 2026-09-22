"""Unit tests for Phase H3 Task H3-T04: Soft-Gate Timing & CLI --strict Flag."""

import asyncio
import unittest
from antinode_norma.server.mcp_server import list_tools


class TestCLIStrictH3T04(unittest.TestCase):
    def test_mcp_tools_soft_gate_description(self):
        tools = asyncio.run(list_tools())
        gate_tool = next(t for t in tools if t.name == "run_quality_gates")
        self.assertIn("ADR-001 v6 §10", gate_tool.description)


if __name__ == "__main__":
    unittest.main()
