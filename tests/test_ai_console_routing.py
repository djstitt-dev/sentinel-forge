import unittest
from types import SimpleNamespace

from sentinel_forge.ai_console import _requested_tool, respond_to_operator, run_console
from sentinel_forge.ai_engine import AiResponse, ToolResult


class FakeEngine:
    def __init__(self):
        self.calls = []

    def execute_tool(self, name, args, *, operator_approved=False):
        self.calls.append(("tool", name, args, operator_approved))
        return ToolResult(
            tool=name,
            ok=True,
            summary='{"cpu_count":4,"memory_available_bytes":123}',
            evidence=(),
        )

    def ask(self, command, *, context=""):
        self.calls.append(("ask", command, context))
        return AiResponse("fake", command, "evidence-backed answer", ())


class ConsoleRoutingTests(unittest.TestCase):
    def test_hardware_usage_routes_to_baseline(self):
        self.assertEqual(
            "system_baseline",
            _requested_tool("Review the current hardware usage on forge again."),
        )

    def test_courier_question_gets_knowledge_tool(self):
        self.assertEqual("network_knowledge", _requested_tool("Explain the Courier trust model."))

    def test_resource_request_tool_then_model_with_evidence(self):
        engine = FakeEngine()
        out = respond_to_operator(engine, "Review current hardware usage")
        self.assertEqual("evidence-backed answer", out)
        self.assertEqual("tool", engine.calls[0][0])
        self.assertFalse(engine.calls[0][3])
        self.assertEqual("ask", engine.calls[1][0])
        self.assertIn("CURRENT TOOL EVIDENCE", engine.calls[1][2])
        self.assertIn('"cpu_count":4', engine.calls[1][2])

    def test_clear_is_console_command_not_model_prompt(self):
        engine = FakeEngine()
        inputs = iter(["clear", "exit"])
        outputs = []
        run_console(engine, input_fn=lambda _: next(inputs), output_fn=outputs.append)
        self.assertEqual([], engine.calls)
        self.assertTrue(any("\033[2J" in x for x in outputs))


if __name__ == "__main__":
    unittest.main()

class EvidenceSemanticsTests(unittest.TestCase):
    def test_health_context_defines_null_as_unknown(self):
        class Provider:
            provider_id = "test-provider"
            def respond(self, command, context):
                self.context = context
                return context
        provider = Provider()
        from sentinel_forge.ai_engine import ForgeAiEngine, Tool, ToolResult
        engine = ForgeAiEngine(
            provider,
            tools=(Tool(
                name="forge_health",
                mutating=False,
                handler=lambda _: ToolResult(
                    tool="forge_health",
                    ok=True,
                    summary='{"model_digest_verified":null}',
                    evidence=(),
                ),
            ),),
        )
        out = respond_to_operator(engine, "Run a system health test")
        self.assertIn("null means NOT CHECKED or UNKNOWN", out)
        self.assertIn("do not say you initiated", out)
        self.assertIn("Do not infer a digest mismatch", out)

class SentinelPeerKnowledgeRoutingTests(unittest.TestCase):
    def test_peer_questions_route_to_offline_knowledge(self):
        for q in (
            "What do you know about Watchtower?",
            "Explain Scribe's role",
            "Tell me everything about Reaper",
        ):
            with self.subTest(q=q):
                self.assertEqual("network_knowledge",_requested_tool(q))
