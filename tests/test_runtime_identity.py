import unittest

from sentinel_forge.runtime_identity import DEFAULT_IDENTITY


class RuntimeIdentityTests(unittest.TestCase):
    def test_default_identity_is_operator_visible_and_bounded(self):
        text = DEFAULT_IDENTITY.render()
        self.assertIn("Sentinel Forge AI", text)
        self.assertIn("Runtime: local persistent / llama.cpp loopback", text)
        self.assertIn("Model: Qwen3-8B-Q4_K_M", text)
        self.assertIn("Tools: system_baseline, forge_health, network_knowledge, network_interfaces", text)
        self.assertIn("Authority: operator-gated; model output is advisory", text)
        self.assertIn("Build: forge-ai-local-v10", text)


if __name__ == "__main__":
    unittest.main()
