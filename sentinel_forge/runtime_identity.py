"""Operator-visible Sentinel Forge AI runtime identity."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeIdentity:
    product: str
    runtime: str
    model: str
    tools: tuple[str, ...]
    authority: str
    build: str

    def render(self) -> str:
        tool_text = ", ".join(self.tools) if self.tools else "none"
        return "\n".join(
            (
                self.product,
                f"Runtime: {self.runtime}",
                f"Model: {self.model}",
                f"Tools: {tool_text}",
                f"Authority: {self.authority}",
                f"Build: {self.build}",
            )
        )


DEFAULT_IDENTITY = RuntimeIdentity(
    product="Sentinel Forge AI",
    runtime="local persistent / llama.cpp loopback",
    model="Qwen3-8B-Q4_K_M",
    tools=("system_baseline", "forge_health", "network_knowledge", "network_interfaces", "network_routes", "network_dns", "network_neighbors", "network_listeners", "network_link_stats", "network_health"),
    authority="operator-gated; model output is advisory",
    build="forge-ai-local-v10",
)
