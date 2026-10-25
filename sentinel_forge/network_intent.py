"""Typed deterministic intent routing for Forge networking questions."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto

class NetworkIntent(Enum):
    NONE=auto()
    LOCAL_ADDRESS=auto()
    ROUTES=auto()
    DEFAULT_GATEWAY=auto()
    DNS=auto()
    NEIGHBORS=auto()
    LISTENERS=auto()
    LINK_STATS=auto()
    HEALTH=auto()
    KNOWLEDGE=auto()

@dataclass(frozen=True)
class IntentDecision:
    intent: NetworkIntent
    confidence: str

def classify_network_intent(text: str) -> IntentDecision:
    n=" ".join(text.lower().split())
    words=set(n.replace("?","").replace(",","").split())
    local_ref=bool(words & {"forge","your","you","my","system","host","machine","local","current"}) or any(
        p in n for p in ("this system","this host","this machine")
    )
    if ("ip address" in n or "ipv4 address" in n or "ipv6 address" in n) and local_ref:
        return IntentDecision(NetworkIntent.LOCAL_ADDRESS,"high")
    if "network health" in n or "network status" in n or "network diagnostics" in n:
        return IntentDecision(NetworkIntent.HEALTH,"high")
    if "default gateway" in n or ("gateway" in words and local_ref):
        return IntentDecision(NetworkIntent.DEFAULT_GATEWAY,"high")
    if any(p in n for p in ("routing table","show routes","show route","current routes")):
        return IntentDecision(NetworkIntent.ROUTES,"high")
    if ("dns" in words or "resolver" in words or "nameserver" in words) and local_ref:
        return IntentDecision(NetworkIntent.DNS,"high")
    if any(p in n for p in ("neighbor table","arp table","ndp table")):
        return IntentDecision(NetworkIntent.NEIGHBORS,"high")
    if any(p in n for p in ("listening ports","open listeners","listening sockets","what ports are listening")):
        return IntentDecision(NetworkIntent.LISTENERS,"high")
    if any(p in n for p in ("interface statistics","link statistics","network statistics")):
        return IntentDecision(NetworkIntent.LINK_STATS,"high")
    return IntentDecision(NetworkIntent.NONE,"none")
