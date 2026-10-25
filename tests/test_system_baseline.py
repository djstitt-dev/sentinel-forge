import json
import tempfile
import unittest
from pathlib import Path

from sentinel_forge.ai_runtime import build_local_engine
from sentinel_forge.system_baseline import baseline_tool, collect_system_baseline, write_baseline_record


class SystemBaselineTests(unittest.TestCase):
    def test_collects_bounded_read_only_telemetry(self):
        b = collect_system_baseline()
        self.assertGreater(b.cpu_count, 0)
        self.assertGreater(b.memory_total_bytes, 0)
        self.assertGreater(b.root_total_bytes, 0)
        self.assertGreaterEqual(b.memory_available_bytes, 0)
        self.assertGreaterEqual(b.root_free_bytes, 0)

    def test_tool_returns_structured_json(self):
        d = json.loads(baseline_tool("ignored operator input"))
        self.assertIn("cpu_count", d)
        self.assertIn("memory_total_bytes", d)
        self.assertIn("root_free_bytes", d)

    def test_evidence_record_is_json_and_exclusive(self):
        with tempfile.TemporaryDirectory() as td:
            p = write_baseline_record(td)
            self.assertTrue(p.is_file())
            d = json.loads(p.read_text())
            self.assertIn("collected_at_utc", d)
            self.assertIn("hostname", d)

    def test_runtime_registers_nonmutating_baseline_tool(self):
        engine = build_local_engine()
        tool = engine.tools["system_baseline"]
        self.assertFalse(tool.mutating)
        result = engine.execute_tool("system_baseline", "anything", operator_approved=False)
        self.assertTrue(result.ok)
        self.assertIn("memory_total_bytes", result.summary)


if __name__ == "__main__":
    unittest.main()
