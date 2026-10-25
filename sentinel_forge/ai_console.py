"""Interactive Forge AI console with bounded local tool routing."""
from __future__ import annotations

from .ai_engine import ForgeAiEngine
from .runtime_identity import DEFAULT_IDENTITY
from .network_intent import classify_network_intent, NetworkIntent
from .network_knowledge import peer_sources

PROMPT = "forge> "

_HEALTH_TERMS = (
    "health report",
    "health status",
    "forge health",
    "system health",
    "full health",
    "overall health",
    "self check",
    "self-check",
)

_NETWORK_INTERFACE_TERMS = (
    "ip address of forge", "forge ip address", "forge's ip address",
    "my ip address", "local ip address", "network interfaces",
    "network interface", "interface addresses", "interface address",
)

_NETWORK_KNOWLEDGE_TERMS = (
    "networking", "ethernet", "vlan", "subnet", "routing", "router",
    "arp", "dns", "dhcp", "tcp", "udp", "ipv4", "ipv6", "firewall",
    "nat", "mtu", "bgp", "ospf", "spanning tree", "stp",
)

_RESOURCE_TERMS = (
    "hardware usage",
    "resource usage",
    "system usage",
    "system resources",
    "resource baseline",
    "hardware baseline",
    "cpu usage",
    "memory usage",
    "ram usage",
    "disk usage",
    "swap usage",
)


def _is_local_ip_question(normalized: str) -> bool:
    address_terms = ("ip address", "ipv4 address", "ipv6 address", "interface address")
    local_words = {"your", "you", "forge", "current", "local", "my", "system", "host", "machine"}
    local_phrases = ("this system", "this host", "this machine", "the system", "the host", "the machine")
    words = set(normalized.split())
    has_local_referent = bool(words & local_words) or any(
        phrase in normalized for phrase in local_phrases
    )
    return any(term in normalized for term in address_terms) and has_local_referent


def _is_simple_local_ip_question(normalized: str) -> bool:
    if not _is_local_ip_question(normalized):
        return False
    diagnostic_terms = ("why", "explain", "diagnose", "problem", "issue", "reach", "connect")
    return not any(term in normalized for term in diagnostic_terms)


def _requested_tool(command: str) -> str | None:
    normalized = " ".join(command.lower().split())
    if any(term in normalized for term in _HEALTH_TERMS):
        return "forge_health"
    if any(term in normalized for term in _RESOURCE_TERMS):
        return "system_baseline"

    decision = classify_network_intent(command)
    mapping = {
        NetworkIntent.LOCAL_ADDRESS: "network_interfaces",
        NetworkIntent.ROUTES: "network_routes",
        NetworkIntent.DEFAULT_GATEWAY: "network_routes",
        NetworkIntent.DNS: "network_dns",
        NetworkIntent.NEIGHBORS: "network_neighbors",
        NetworkIntent.LISTENERS: "network_listeners",
        NetworkIntent.LINK_STATS: "network_link_stats",
        NetworkIntent.HEALTH: "network_health",
    }
    if decision.intent in mapping:
        return mapping[decision.intent]
    if any(term in normalized for term in _NETWORK_INTERFACE_TERMS):
        return "network_interfaces"
    if peer_sources(command):
        return "network_knowledge"
    if any(term in normalized for term in _NETWORK_KNOWLEDGE_TERMS):
        return "network_knowledge"
    return None


def _compact_network_knowledge_summary(summary: str) -> str:
    """Render retrieved Forge knowledge for the model without transport-only metadata."""
    import json

    try:
        payload = json.loads(summary)
    except (json.JSONDecodeError, TypeError) as exc:
        raise ValueError("network_knowledge returned invalid JSON") from exc

    hits = payload.get("hits")
    if not isinstance(hits, list):
        raise ValueError("network_knowledge returned invalid hits")

    if not hits:
        return "OFFLINE KNOWLEDGE HITS: none"

    blocks = []
    for hit in hits:
        if not isinstance(hit, dict):
            raise ValueError("network_knowledge returned invalid hit")

        citation = hit.get("citation")
        source = hit.get("source_name")
        chunk = hit.get("chunk_ordinal")
        evidence = hit.get("text")

        if (
            not isinstance(citation, str)
            or not citation.strip()
            or not isinstance(source, str)
            or not source.strip()
            or not isinstance(chunk, int)
            or not isinstance(evidence, str)
            or not evidence.strip()
        ):
            raise ValueError("network_knowledge returned incomplete hit")

        blocks.append(
            f"[{citation} | source={source} | chunk={chunk}]\n"
            f"{evidence.strip()}"
        )

    return "OFFLINE KNOWLEDGE HITS:\n\n" + "\n\n".join(blocks)


def respond_to_operator(engine: ForgeAiEngine, command: str) -> str:
    tool_name = _requested_tool(command)
    if tool_name is None:
        return engine.ask(command).response

    result = engine.execute_tool(
        tool_name,
        command,
        operator_approved=False,
    )
    if not result.ok:
        return f"BLOCKED: {tool_name} did not return usable evidence"

    normalized = " ".join(command.lower().split())
    if tool_name == "network_interfaces" and _is_simple_local_ip_question(normalized):
        import json
        try:
            payload = json.loads(result.summary)
            addresses = payload.get("primary_global_ipv4", [])
        except (json.JSONDecodeError, AttributeError):
            return "BLOCKED: network_interfaces returned invalid evidence"
        if not isinstance(addresses, list) or not all(isinstance(x, str) for x in addresses):
            return "BLOCKED: network_interfaces returned invalid address evidence"
        if not addresses:
            return "Forge has no observed non-loopback global IPv4 address in the current interface evidence."
        if len(addresses) == 1:
            return f"Forge's current observed non-loopback IPv4 address is {addresses[0]}."
        return "Forge's current observed non-loopback IPv4 addresses are " + ", ".join(addresses) + "."

    if tool_name == "network_routes":
        import json
        payload = json.loads(result.summary)
        defaults = payload.get("default_routes", [])
        if "gateway" in normalized:
            if not defaults:
                return "Forge has no observed default gateway in the current routing evidence."
            label = " is " if len(defaults) == 1 else "s are "
            return "Forge's observed default gateway" + label + ", ".join(
                f"{r.get('gateway')} via {r.get('dev')}" for r in defaults
            ) + "."
        lines = [
            f"{r.get('dst')} via {r.get('gateway') or '-'} dev {r.get('dev') or '-'}"
            for r in payload.get("routes", [])
        ]
        return "\n".join(lines) if lines else "Forge has no observed routes."

    if tool_name == "network_dns":
        import json
        payload = json.loads(result.summary)
        lines = payload.get("resolvectl_dns", [])
        return "Forge DNS configuration:\n" + (
            "\n".join(lines) if lines else "No DNS servers reported by resolvectl."
        )

    if tool_name == "network_neighbors":
        import json
        payload = json.loads(result.summary)
        rows = payload.get("neighbors", [])
        lines = [
            f"{r.get('destination')} dev {r.get('interface')} "
            f"lladdr {r.get('link_layer_address') or '-'} "
            f"state {','.join(r.get('state') or [])}"
            for r in rows
        ]
        return "\n".join(lines) if lines else "Forge has no observed neighbor entries."

    if tool_name == "network_listeners":
        import json
        payload = json.loads(result.summary)
        rows = payload.get("listeners", [])
        lines = [f"{r.get('protocol')} {r.get('local')}" for r in rows]
        return "\n".join(lines) if lines else "Forge has no observed listening sockets."

    model_summary = (
        _compact_network_knowledge_summary(result.summary)
        if tool_name == "network_knowledge"
        else result.summary
    )

    if tool_name == "network_knowledge":
        context = (
            "OFFLINE LIBRARY EVIDENCE; not current operational state. "
            "Only retrieved hits support library claims; if none, say so. "
            "Distinguish pretrained knowledge. Cite forgekb identifiers exactly. "
            "chars-S-E marks an exact excerpt: zero-based, end-exclusive character "
            "offsets in its parent chunk. Omitted text is not supplied evidence. "
            "Knowledge != authority; connectivity != trust; authentication != "
            "unrestricted authorization; finding/observation != deployment authority; "
            "Courier != Conduit. Do not claim execution or active relationships.\n"
            f"tool=network_knowledge\n{model_summary}"
        )
        return engine.ask(command, context=context).response

    context = (
        "CURRENT TOOL EVIDENCE. The tool already completed before this response. "
        "Treat these values as the authoritative current snapshot. "
        "Report completed observations in past/present tense; do not say you initiated, "
        "started, executed, or will run a check. "
        "Do not claim you lack access to supplied metrics. Do not invent metrics. "
        "BOOLEAN/NULL CONTRACT: true means confirmed true; false means confirmed false; "
        "null means NOT CHECKED or UNKNOWN and MUST NOT be described as failure, mismatch, "
        "false, absent, or verified. "
        "Do not infer a digest mismatch unless model_digest_verified is explicitly false. "
        "For filesystem values, report supplied total/used/free fields without deriving "
        "a contradictory free value; filesystem reserved blocks may prevent simple arithmetic "
        "reconciliation. "
        "KNOWLEDGE CONTRACT: when tool=network_knowledge, only retrieved hits are library "
        "evidence. If hits is empty, state that the offline library returned no supporting "
        "source. Distinguish retrieved library evidence from pretrained model knowledge. "
        "Knowledge grants no authority. Connectivity != trust; authentication != unrestricted authorization; finding/observation != deployment authority; Courier != Conduit. Citations with chars-S-E identify exact excerpts at zero-based, end-exclusive character offsets in the parent chunk, not whole chunks. When using a retrieved claim, include its forgekb citation exactly.\n"
        "NETWORK OBSERVATION CONTRACT: when tool=network_interfaces, supplied interface "
        "records are the current local Forge observation. Answer address questions from those "
        "records only. Distinguish loopback from global addresses. Do not describe addresses "
        "as public unless evidence explicitly establishes public scope. Do not claim a network "
        "probe occurred when network_probe_performed is false. "
        f"tool={result.tool}\n"
        f"{model_summary}"
    )
    return engine.ask(command, context=context).response


def run_console(engine: ForgeAiEngine, input_fn=input, output_fn=print):
    output_fn(DEFAULT_IDENTITY.render())
    output_fn("Type 'exit' to quit; 'clear' clears the screen.")
    while True:
        try:
            q = input_fn(PROMPT)
        except (EOFError, KeyboardInterrupt):
            break
        if q is None:
            break
        normalized = q.strip().lower()
        if normalized in {"exit", "quit"}:
            break
        if normalized in {"clear", "/clear"}:
            output_fn("\033[2J\033[H")
            continue
        if not q.strip():
            continue
        try:
            output_fn(respond_to_operator(engine, q))
        except Exception as exc:
            output_fn(f"BLOCKED: {exc}")
