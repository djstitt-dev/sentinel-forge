import json
from pathlib import Path
import tempfile
import unittest

from sentinel_forge.enrollment import EnrollmentError
from sentinel_forge.knowledge_library import KnowledgeLibrary, chunk_text, knowledge_tool


class KnowledgeLibraryTests(unittest.TestCase):
    def test_deterministic_chunking(self):
        text=("Ethernet frames carry layer two data.\n\n" * 100).strip()
        self.assertEqual(chunk_text(text), chunk_text(text))
        self.assertGreater(len(chunk_text(text)), 1)

    def test_ingest_search_and_provenance(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); src=root/"rfc-note.md"; db=root/"kb.sqlite3"
            src.write_text("# ARP\n\nARP resolves IPv4 protocol addresses to link-layer addresses on a local network.")
            lib=KnowledgeLibrary(db)
            record=lib.ingest(src.resolve())
            self.assertEqual("ingested", record["status"])
            hit=lib.search("ARP IPv4")[0]
            self.assertEqual(record["source_sha256"], hit.source_sha256)
            self.assertTrue(hit.citation.startswith("forgekb:"))
            self.assertEqual({"source_count":1,"chunk_count":1},lib.stats())

    def test_duplicate_is_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); src=root/"x.txt"; db=root/"kb.sqlite3"
            src.write_text("Routing tables select paths for packets.")
            lib=KnowledgeLibrary(db)
            lib.ingest(src.resolve())
            second=lib.ingest(src.resolve())
            self.assertEqual("already_ingested", second["status"])
            self.assertEqual(1,lib.stats()["source_count"])

    def test_rejects_symlink_and_unapproved_type(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); real=root/"x.txt"; real.write_text("x")
            link=root/"link.txt"; link.symlink_to(real)
            lib=KnowledgeLibrary(root/"kb.sqlite3")
            with self.assertRaises(EnrollmentError): lib.ingest(link.resolve(strict=False) if False else link.absolute())
            bad=root/"x.pdf"; bad.write_bytes(b"x")
            with self.assertRaises(EnrollmentError): lib.ingest(bad.resolve())

    def test_tool_returns_cited_hits(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); src=root/"dns.md"; db=root/"kb.sqlite3"
            src.write_text("DNS maps domain names to resource records.")
            lib=KnowledgeLibrary(db); lib.ingest(src.resolve())
            payload=json.loads(knowledge_tool("DNS",db))
            self.assertEqual(1,payload["library"]["source_count"])
            self.assertTrue(payload["hits"][0]["citation"].startswith("forgekb:"))


if __name__=="__main__":
    unittest.main()

class KnowledgeRoutingTests(unittest.TestCase):
    def test_networking_language_routes_to_library(self):
        from sentinel_forge.ai_console import _requested_tool
        self.assertEqual("network_knowledge", _requested_tool("Explain how ARP works"))
        self.assertEqual("network_knowledge", _requested_tool("Teach me about VLANs"))

    def test_non_network_question_does_not_route(self):
        from sentinel_forge.ai_console import _requested_tool
        self.assertIsNone(_requested_tool("Tell me a joke"))

    def test_runtime_registers_read_only_knowledge(self):
        from sentinel_forge.ai_runtime import build_local_engine
        engine=build_local_engine()
        self.assertFalse(engine.tools["network_knowledge"].mutating)

class KnowledgeRankingTests(unittest.TestCase):
    def test_all_terms_preferred_over_incidental_single_term(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); db=root/"kb.sqlite3"
            arp=root/"arp.txt"; dhcp=root/"dhcp.txt"
            arp.write_text("ARP maps protocol address to hardware address on the local network.")
            dhcp.write_text("DHCP may check an address with ARP before assigning a lease.")
            lib=KnowledgeLibrary(db); lib.ingest(arp.resolve()); lib.ingest(dhcp.resolve())
            self.assertEqual("arp.txt",lib.search("ARP protocol address hardware address")[0].source_name)

class NetworkTopicRoutingTests(unittest.TestCase):
    def test_canonical_topic_source_binding(self):
        from sentinel_forge.network_knowledge import canonical_sources
        self.assertEqual(("rfc826.txt",),canonical_sources("How does ARP work?"))
        self.assertEqual(("rfc9293.txt",),canonical_sources("TCP connection state machine"))
        self.assertEqual(("rfc8200.txt",),canonical_sources("Explain the IPv6 base header"))
        self.assertEqual(("rfc1034.txt","rfc1035.txt"),canonical_sources("DNS resolution"))


class ExpandedAuthorityRoutingTests(unittest.TestCase):
    def test_security_and_linux_authorities(self):
        from sentinel_forge.network_knowledge import canonical_sources
        self.assertEqual(("nist-sp800-207.txt",),canonical_sources("Explain zero trust architecture"))
        self.assertEqual(("nist-sp800-41r1.txt",),canonical_sources("How should firewall policy be managed?"))
        self.assertEqual(("linux-ip-sysctl.txt",),canonical_sources("What does rp_filter do?"))
        self.assertEqual(("linux-netdevices.txt",),canonical_sources("Explain Linux NAPI network device behavior"))
        self.assertEqual(("linux-scaling.txt",),canonical_sources("Explain RPS and RSS"))


class SentinelPeerRoutingTests(unittest.TestCase):
    def test_peer_source_binding(self):
        from sentinel_forge.network_knowledge import peer_sources
        self.assertEqual(("watchtower.md",),peer_sources("What is Watchtower responsible for?"))
        self.assertEqual(("scribe.md",),peer_sources("Explain Scribe release authority"))
        self.assertEqual(("reaper.md",),peer_sources("What do we know about Reaper?"))
        self.assertEqual(
            ("scribe.md", "reaper.md"),
            peer_sources("Compare Scribe and Reaper"),
        )
