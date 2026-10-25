"""Transport contracts with no production transport implementation."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping, Any, Protocol

@dataclass(frozen=True)
class TransportOutcome:
    state: str
    acknowledgement: str | None = None

class Transport(Protocol):
    def effect(self, request: Mapping[str, Any]) -> TransportOutcome: ...

class DisconnectedTransport:
    def effect(self, request: Mapping[str, Any]) -> TransportOutcome:
        return TransportOutcome("NOT_ATTEMPTED")

class SimulatedTransport:
    """Test-only deterministic effect simulator."""
    def __init__(self, state: str):
        if state not in {"TRANSFERRED","REJECTED","PARTIAL","OUTCOME_UNKNOWN"}:
            raise ValueError("unsupported simulated outcome")
        self.state=state
        self.calls=0
    def effect(self, request: Mapping[str, Any]) -> TransportOutcome:
        self.calls += 1
        ack = "SIMULATED_ACK" if self.state == "TRANSFERRED" else None
        return TransportOutcome(self.state, ack)
