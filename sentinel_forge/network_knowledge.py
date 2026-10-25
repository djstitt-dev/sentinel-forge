"""Deterministic networking-topic routing over the offline Forge knowledge library."""
from __future__ import annotations

from dataclasses import dataclass
import json
import re
from .knowledge_library import KnowledgeHit, KnowledgeLibrary, DEFAULT_DB

ARCHITECTURE_SOURCES = {
    "remote peer": ("remote-peer-enrollment.md",),
    "peer enrollment": ("remote-peer-enrollment.md",),
    "remote configuration": ("remote-peer-enrollment.md",),
    "secure communication": ("remote-peer-enrollment.md",),
}

PEER_SOURCES = {
    "watchtower": ("watchtower.md",),
    "scribe": ("scribe.md",),
    "reaper": ("reaper.md",),
    "conduit": ("conduit.md",),
    "courier": ("courier.md",),
}

MULTI_PEER_EVIDENCE_CHAR_BUDGET = 6000

def peer_sources(query: str) -> tuple[str, ...]:
    """Return every explicitly named Sentinel peer source in deterministic order."""
    words = set(re.findall(r"[a-z0-9_-]+", query.lower()))
    sources: list[str] = []

    for name, peer_sources_for_name in PEER_SOURCES.items():
        if name not in words:
            continue
        for source in peer_sources_for_name:
            if source not in sources:
                sources.append(source)

    return tuple(sources)

def primary_peer_source(
    query: str,
    preferred: tuple[str, ...],
) -> str | None:
    """Return the earliest explicitly named peer, including possessive forms."""
    normalized = query.lower()
    positions: list[tuple[int, str]] = []

    for source in preferred:
        name = source.removesuffix(".md")
        match = re.search(
            rf"\b{re.escape(name)}(?:['’]s)?\b",
            normalized,
        )
        if match:
            positions.append((match.start(), source))

    return min(positions)[1] if positions else None


@dataclass(frozen=True)
class EvidenceExcerpt:
    """An exact span of an immutable hit, never a replacement KnowledgeHit.

    Offsets are zero-based Python Unicode character offsets, end exclusive.
    The citation identifies both the parent chunk and the quoted span.
    """
    parent: KnowledgeHit
    start: int
    end: int

    @property
    def citation(self):
        return f"{self.parent.citation}:chars-{self.start}-{self.end}"

    @property
    def text(self):
        return self.parent.text[self.start:self.end]

    def __getattr__(self, name):
        return getattr(self.parent, name)


def evidence_block(hit):
    return (f"[{hit.citation} | source={hit.source_name} | chunk={hit.chunk_ordinal}]\n"
            f"{hit.text.strip()}")


def evidence_size(hits):
    return len("OFFLINE KNOWLEDGE HITS:\n\n" + "\n\n".join(evidence_block(h) for h in hits))


def _fit_excerpt(hit, allowance):
    # Prefer a complete paragraph/sentence boundary. If a source has no such
    # boundary, quote a word-bounded span with explicit offsets, not a summary.
    end = min(len(hit.text), allowance)
    while end > 0:
        unit = EvidenceExcerpt(hit, 0, end)
        excess = len(evidence_block(unit)) - allowance
        if excess <= 0:
            break
        end -= excess
    if end <= 0:
        raise ValueError("evidence budget too small for source provenance")
    boundaries = [m.end() for m in re.finditer(r"[.!?](?=\s|$)|\n\n", hit.text[:end])]
    if boundaries:
        end = boundaries[-1]
    elif end < len(hit.text):
        end = hit.text.rfind(" ", 0, end)
    if end <= 0:
        raise ValueError("evidence budget too small for a source excerpt")
    return EvidenceExcerpt(hit, 0, end)


def balanced_multi_peer_hits(
    lib: KnowledgeLibrary,
    query: str,
    preferred: tuple[str, ...],
    budget: int = MULTI_PEER_EVIDENCE_CHAR_BUDGET,
):
    """Coverage first; budget includes the exact model-facing citation framing."""
    candidates = []
    for source in dict.fromkeys(preferred):
        hits = lib.search_sources(query, (source,), limit=1)
        if not hits:
            hits = lib.search_sources(source.removesuffix(".md"), (source,), limit=1)
        if hits:
            candidates.append(hits[0])
    if not candidates:
        return []
    selected = candidates
    if evidence_size(selected) > budget:
        allowance = (budget - len("OFFLINE KNOWLEDGE HITS:\n\n")
                     - 2 * (len(candidates) - 1)) // len(candidates)
        selected = [h if len(evidence_block(h)) <= allowance else _fit_excerpt(h, allowance)
                    for h in candidates]
    keys = {(h.source_id, h.chunk_ordinal) for h in selected}
    primary = primary_peer_source(query, preferred)
    if primary:
        for hit in lib.search_sources(query, (primary,), limit=5):
            if (hit.source_id, hit.chunk_ordinal) in keys:
                continue
            if evidence_size([*selected, hit]) <= budget:
                selected = [*selected, hit]
                break
    return selected


TOPICS = (
    (("zero trust", "zta"), ("nist-sp800-207.txt",)),
    (("firewall policy", "firewall"), ("nist-sp800-41r1.txt",)),
    (("sysctl", "ip_forward", "rp_filter", "tcp_syncookies"), ("linux-ip-sysctl.txt",)),
    (("netdevice", "network device", "napi"), ("linux-netdevices.txt",)),
    (("rss", "rps", "rfs", "xps", "receive packet steering", "receive side scaling"), ("linux-scaling.txt",)),
    (("arp", "address resolution protocol"), ("rfc826.txt",)),
    (("udp", "user datagram protocol"), ("rfc768.txt",)),
    (("dns", "domain name system"), ("rfc1034.txt","rfc1035.txt")),
    (("dhcp", "dynamic host configuration protocol"), ("rfc2131.txt",)),
    (("ospf", "open shortest path first"), ("rfc2328.txt",)),
    (("bgp", "border gateway protocol"), ("rfc4271.txt",)),
    (("ipsec", "ip security"), ("rfc4301.txt",)),
    (("cidr", "classless inter-domain routing", "subnet"), ("rfc4632.txt",)),
    (("neighbor discovery", "ndp"), ("rfc4861.txt",)),
    (("ipv6", "internet protocol version 6"), ("rfc8200.txt",)),
    (("tcp", "transmission control protocol"), ("rfc9293.txt",)),
)


def canonical_sources(query: str) -> tuple[str, ...]:
    normalized=" ".join(query.lower().split())
    words=set(re.findall(r"[a-z0-9_]+", normalized))
    for aliases,sources in TOPICS:
        for alias in aliases:
            if " " in alias:
                if alias in normalized:
                    return sources
            elif alias in words:
                return sources
    return ()


def network_knowledge_tool(query: str, path=DEFAULT_DB) -> str:
    lib=KnowledgeLibrary(path)
    peer_preferred=peer_sources(query)
    normalized=query.lower()
    architecture_preferred=next((sources for phrase,sources in ARCHITECTURE_SOURCES.items() if phrase in normalized),())
    preferred=peer_preferred or architecture_preferred or canonical_sources(query)
    hits=lib.search(query,limit=10)
    if len(peer_preferred) > 1 or peer_preferred in (("conduit.md",), ("courier.md",)):
        hits=balanced_multi_peer_hits(lib,query,peer_preferred)
    elif preferred:
        scoped=lib.search_sources(query,preferred,limit=5)
        if not scoped:
            aliases=next((a for a,sources in TOPICS if sources==preferred),
                         tuple(source.removesuffix(".md") for source in preferred))
            reduced=query.lower()
            for alias in sorted(aliases,key=len,reverse=True):
                reduced=re.sub(r"\b"+re.escape(alias)+r"\b"," ",reduced)
            reduced=" ".join(reduced.split())
            retry=reduced or aliases[0]
            scoped=lib.search_sources(retry,preferred,limit=5)
        hits=scoped
    else:
        hits=hits[:5]
    return json.dumps({
        "query":query,
        "canonical_sources":preferred,
        "library":lib.stats(),
        "hits":[{
            "citation":h.citation,"source_name":h.source_name,
            "source_sha256":h.source_sha256,"chunk_ordinal":h.chunk_ordinal,
            "text":h.text,"score":h.score,
            **({"evidence_kind":"exact_excerpt", "parent_citation":h.parent.citation,
                "char_start":h.start,"char_end":h.end}
               if isinstance(h,EvidenceExcerpt) else {"evidence_kind":"whole_chunk"}),
        } for h in hits],
    },sort_keys=True)
