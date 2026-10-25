"""Production-local wiring for the Sentinel Forge offline AI console."""
from __future__ import annotations

import os
from pathlib import Path

from .ai_console import run_console
from .ai_engine import ForgeAiEngine, Tool, ToolResult
from .enrollment import EnrollmentError
from .persistent_model import PersistentLocalModel, PersistentModelConfig
from .system_baseline import baseline_tool
from .forge_health import forge_health_tool
from .network_knowledge import network_knowledge_tool
from .network_interfaces import network_interfaces_tool
from .network_observation import (
    as_json, observe_routes, observe_neighbors, observe_listeners,
    observe_dns, observe_interface_stats, network_health,
)

DEFAULT_EXECUTABLE = "/usr/bin/llama-server"
DEFAULT_MODEL = str(
    Path.home() / "Project-Sentinel-Forge" / "models" / "qwen3-8b" / "Qwen3-8B-Q4_K_M.gguf"
)


def build_local_engine() -> ForgeAiEngine:
    executable = os.environ.get("SENTINEL_FORGE_LLM_EXECUTABLE", DEFAULT_EXECUTABLE)
    model_path = os.environ.get("SENTINEL_FORGE_LLM_MODEL", DEFAULT_MODEL)
    if not Path(executable).is_file():
        raise EnrollmentError("local model executable unavailable")
    if not Path(model_path).is_file():
        raise EnrollmentError("local model artifact unavailable")

    provider = PersistentLocalModel(
        PersistentModelConfig(
            executable=executable,
            model_path=model_path,
            host="127.0.0.1",
            port=18081,
            timeout_seconds=300,
            startup_seconds=180,
            max_tokens=1024,
            thinking=False,
        )
    )
    def system_baseline_handler(_: str) -> ToolResult:
        return ToolResult(
            tool="system_baseline",
            ok=True,
            summary=baseline_tool(""),
            evidence=(),
        )

    def forge_health_handler(_: str) -> ToolResult:
        return ToolResult(
            tool="forge_health",
            ok=True,
            summary=forge_health_tool(""),
            evidence=(),
        )

    def network_knowledge_handler(query: str) -> ToolResult:
        return ToolResult(
            tool="network_knowledge",
            ok=True,
            summary=network_knowledge_tool(query),
            evidence=(),
        )

    def network_interfaces_handler(_: str) -> ToolResult:
        return ToolResult(
            tool="network_interfaces",
            ok=True,
            summary=network_interfaces_tool(""),
            evidence=(),
        )

    def network_health_handler(_: str) -> ToolResult:
        return ToolResult(tool="network_health", ok=True, summary=as_json(network_health()), evidence=())

    def network_routes_handler(_: str) -> ToolResult:
        return ToolResult(tool="network_routes", ok=True, summary=as_json(observe_routes()), evidence=())

    def network_dns_handler(_: str) -> ToolResult:
        return ToolResult(tool="network_dns", ok=True, summary=as_json(observe_dns()), evidence=())

    def network_neighbors_handler(_: str) -> ToolResult:
        return ToolResult(tool="network_neighbors", ok=True, summary=as_json(observe_neighbors()), evidence=())

    def network_listeners_handler(_: str) -> ToolResult:
        return ToolResult(tool="network_listeners", ok=True, summary=as_json(observe_listeners()), evidence=())

    def network_link_stats_handler(_: str) -> ToolResult:
        return ToolResult(tool="network_link_stats", ok=True, summary=as_json(observe_interface_stats()), evidence=())

    tools = (
        Tool(
            name="system_baseline",
            mutating=False,
            handler=system_baseline_handler,
        ),
        Tool(
            name="forge_health",
            mutating=False,
            handler=forge_health_handler,
        ),
        Tool(
            name="network_knowledge",
            mutating=False,
            handler=network_knowledge_handler,
        ),
        Tool(
            name="network_interfaces",
            mutating=False,
            handler=network_interfaces_handler,
        ),
        Tool(name="network_routes", mutating=False, handler=network_routes_handler),
        Tool(name="network_dns", mutating=False, handler=network_dns_handler),
        Tool(name="network_neighbors", mutating=False, handler=network_neighbors_handler),
        Tool(name="network_listeners", mutating=False, handler=network_listeners_handler),
        Tool(name="network_link_stats", mutating=False, handler=network_link_stats_handler),
        Tool(name="network_health", mutating=False, handler=network_health_handler),
    )
    return ForgeAiEngine(provider, tools=tools)


def main() -> int:
    engine = build_local_engine()
    provider = engine.provider
    try:
        provider.start()
        run_console(engine)
    finally:
        provider.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
