import json
import unittest

from sentinel_forge.ai_console import _requested_tool
from sentinel_forge.ai_runtime import build_local_engine
from sentinel_forge.forge_health import collect_forge_health, forge_health_tool


class ForgeHealthTests(unittest.TestCase):
    def test_collects_bounded_health_snapshot(self):
        h = collect_forge_health()
        self.assertEqual("sentinel-forge", h["node"]["hostname"])
        self.assertGreater(h["node"]["cpu_count"], 0)
        self.assertTrue(h["local_ai"]["executable_present"])
        self.assertTrue(h["local_ai"]["model_present"])
        self.assertIn("branch", h["repository"])
        self.assertIn("head", h["repository"])
        self.assertTrue(h["sentinel_components"]["ai_engine.py"])
        self.assertFalse(h["security"]["network_probe_performed"])
        self.assertFalse(h["security"]["sudo_used"])
        self.assertFalse(h["security"]["arbitrary_shell_input_accepted"])

    def test_tool_is_json(self):
        h = json.loads(forge_health_tool(""))
        self.assertEqual("read-only", h["security"]["tool_mode"])

    def test_runtime_registers_nonmutating_health_tool(self):
        engine = build_local_engine()
        self.assertFalse(engine.tools["forge_health"].mutating)
        result = engine.execute_tool("forge_health", "", operator_approved=False)
        self.assertTrue(result.ok)
        self.assertIn('"repository"', result.summary)

    def test_health_language_routes_to_health_tool(self):
        self.assertEqual("forge_health", _requested_tool("Give me a full health report."))
        self.assertEqual("forge_health", _requested_tool("What is Forge health status?"))


if __name__ == "__main__":
    unittest.main()
