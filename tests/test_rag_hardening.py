"""Offline tests; fixture databases are temporary and never use DEFAULT_DB."""
from contextlib import closing
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, Mock

from sentinel_forge.ai_console import _compact_network_knowledge_summary, _requested_tool
from sentinel_forge.knowledge_library import KnowledgeLibrary, KnowledgeHit
from sentinel_forge.network_knowledge import (
    PEER_SOURCES, EvidenceExcerpt, balanced_multi_peer_hits, network_knowledge_tool,
    peer_sources, primary_peer_source,
)
from sentinel_forge.persistent_model import clean_model_response, PersistentLocalModel, PersistentModelConfig
from sentinel_forge.enrollment import EnrollmentError


class CoverageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.lib = KnowledgeLibrary(Path(self.tmp.name) / 'knowledge.sqlite3')
        root = Path(__file__).resolve().parents[1]
        for folder in ('sentinel-peers', 'forge-architecture'):
            for source in sorted((root / 'knowledge' / folder).glob('*.md')):
                self.lib.ingest(source)

    def test_component_cases_and_real_rendered_budget(self):
        for query, names in (
            ('Explain Conduit', ['conduit']),
            ('Explain Courier', ['courier']),
            ('Conduit vs Courier', ['conduit', 'courier']),
            ('Reaper Conduit Courier', ['reaper', 'conduit', 'courier']),
            ("Explain Reaper’s relationship to Forge, Scribe, Watchtower, Conduit and Courier", list(PEER_SOURCES)),
        ):
            with self.subTest(query=query):
                self.assertEqual('network_knowledge', _requested_tool(query))
                raw = network_knowledge_tool(query, self.lib.path)
                payload = json.loads(raw)
                self.assertEqual({n+'.md' for n in names}, {h['source_name'] for h in payload['hits']})
                self.assertEqual(raw, network_knowledge_tool(query, self.lib.path))
                if len(names) > 1:
                    self.assertLessEqual(len(_compact_network_knowledge_summary(raw)), 6000)
                keys = [(h['source_sha256'], h['chunk_ordinal']) for h in payload['hits']]
                self.assertEqual(len(keys), len(set(keys)))
                # Retrieve the original stored chunk, independent of excerpt construction.
                import sqlite3
                with closing(sqlite3.connect(self.lib.path)) as con:
                    for h in payload['hits']:
                        text, sid = con.execute('SELECT c.text,s.source_id FROM chunks c JOIN sources s USING(source_id) WHERE s.source_sha256=? AND c.ordinal=?', (h['source_sha256'], h['chunk_ordinal'])).fetchone()
                        parent = f"forgekb:{sid}:chunk-{h['chunk_ordinal']}"
                        if h['evidence_kind'] == 'exact_excerpt':
                            self.assertEqual(text[h['char_start']:h['char_end']], h['text'])
                            self.assertEqual(parent, h['parent_citation'])
                            self.assertEqual(f"{parent}:chars-{h['char_start']}-{h['char_end']}",h['citation'])
                        else:
                            self.assertEqual(text,h['text'])
                            self.assertEqual(parent,h['citation'])

    def test_explicit_names_not_substrings(self):
        self.assertIsNone(_requested_tool('Describe a poem'))
        self.assertEqual((),peer_sources('couriering conduits scribes reapers'))

    def test_primary_depth_and_repeated_source_dedupe(self):
        a=KnowledgeHit('a','reaper.md','digest-a',1,'Reaper facts.',0.0)
        depth=KnowledgeHit('a','reaper.md','digest-a',2,'More Reaper facts.',1.0)
        b=KnowledgeHit('b','courier.md','digest-b',1,'Courier facts.',0.0)
        lib=Mock()
        lib.search_sources.side_effect=lambda q,sources,limit: (a,depth)[:limit] if sources==('reaper.md',) else (b,)
        hits=balanced_multi_peer_hits(lib,"Reaper’s Courier",('courier.md','reaper.md','reaper.md'))
        self.assertEqual([b,a,depth],hits)

    def test_single_peer_unchanged(self):
        for name in ('reaper','scribe','watchtower'):
            q = f'Explain {name}'
            actual=json.loads(network_knowledge_tool(q,self.lib.path))['hits']
            expected=self.lib.search_sources(q,(name+'.md',),limit=5)
            self.assertEqual([(h.citation,h.text) for h in expected],[(h['citation'],h['text']) for h in actual])

    def test_order_possessive_primary(self):
        for q in ("Reaper's Conduit Courier Scribe Watchtower", 'Reaper’s Courier Conduit Watchtower Scribe'):
            self.assertEqual(tuple(n+'.md' for n in PEER_SOURCES),peer_sources(q))
            self.assertEqual('reaper.md',primary_peer_source(q,peer_sources(q)))
            hits=balanced_multi_peer_hits(self.lib,q,peer_sources(q))
            self.assertEqual(list(peer_sources(q)),[h.source_name for h in hits[:5]])

    def test_fallback_non_topics_no_crash(self):
        with patch('sentinel_forge.network_knowledge.KnowledgeLibrary') as cls:
            cls.return_value.search.return_value=()
            cls.return_value.search_sources.return_value=()
            cls.return_value.stats.return_value={}
            for q in ('Conduit', 'Courier', 'Reaper', 'remote peer', 'TCP'):
                self.assertEqual([],json.loads(network_knowledge_tool(q))['hits'])

    def test_excerpt_does_not_mutate_parent_and_small_budget_fails_explicitly(self):
        h=KnowledgeHit('id','conduit.md','digest',1,'A complete sentence. '*200,0.0)
        lib=Mock();lib.search_sources.return_value=(h,)
        result=balanced_multi_peer_hits(lib,'Conduit',('conduit.md',),600)
        self.assertIsInstance(result[0],EvidenceExcerpt)
        self.assertEqual('A complete sentence. '*200,h.text)
        with self.assertRaises(ValueError):
            balanced_multi_peer_hits(lib,'Conduit',('conduit.md',),5)


class ModelHardeningTests(unittest.TestCase):
    def model(self):
        return PersistentLocalModel(PersistentModelConfig('/unused/server','/unused/model'))

    def test_cleanup_preserves_legitimate_content(self):
        for value, expected in (
            ('  </think>\nAnswer.','Answer.'),
            ('<think> \n</think> Answer.','Answer.'),
            ('<think>reasoning</think> Answer.','<think>reasoning</think> Answer.'),
            ('Quote </think> in XML.','Quote </think> in XML.'),
            ('```\n</think>\n```','```\n</think>\n```'),
            ('<think>unfinished','<think>unfinished'),
        ):
            self.assertEqual(expected,clean_model_response(value))

    def test_diagnostics_discard_secret_bytes(self):
        m=self.model();stream=io.BytesIO(b'error secret-token\nwarning /private/path\n')
        m._drain_diagnostics(stream)
        self.assertTrue(stream.closed)
        self.assertEqual(1,m.diagnostics['error_blocks'])
        self.assertNotIn('secret',repr(m.diagnostics))

    def test_kill_and_reap_after_terminate_timeout(self):
        import subprocess
        m=self.model();p=Mock();p.poll.side_effect=[None,-9]
        p.wait.side_effect=[subprocess.TimeoutExpired('test',10),None]
        m._process=p;m.close();p.terminate.assert_called_once();p.kill.assert_called_once()
        self.assertEqual(2,p.wait.call_count)
        m.close()

    def test_start_failure_and_interrupt_cleanup(self):
        for error in (EnrollmentError('startup failed'),KeyboardInterrupt()):
            m=self.model()
            with patch.object(m,'_start',side_effect=error),patch.object(m,'close') as close:
                with self.assertRaises(type(error)):m.start()
                close.assert_called_once()

    def test_early_child_exit_reaps_and_drains(self):
        process=Mock();process.poll.return_value=7
        process.stdout=io.BytesIO(b'error private input')
        m=PersistentLocalModel(PersistentModelConfig('/unused/server','/unused/model'),popen=Mock(return_value=process))
        with patch('sentinel_forge.persistent_model.socket.socket'):
            with self.assertRaisesRegex(EnrollmentError,'exited during startup'):m.start()
        self.assertIsNone(m._process)
        self.assertEqual(7,m.last_exit_code)
        self.assertTrue(process.stdout.closed)
        self.assertIsNone(m._diagnostic_thread)
        self.assertFalse(m._popen.call_args.kwargs['shell'])

    def test_occupied_port_never_launches_child(self):
        m=self.model();m._popen=Mock()
        with patch('sentinel_forge.persistent_model.socket.socket',side_effect=OSError):
            with self.assertRaisesRegex(EnrollmentError,'port unavailable'):m.start()
        m._popen.assert_not_called()

    def test_response_contract_and_empty_cleanup(self):
        for content in ('</think> Answer','</think>'):
            m=self.model();response=Mock();response.read.return_value=json.dumps({'content':content}).encode()
            response.__enter__=Mock(return_value=response);response.__exit__=Mock(return_value=False)
            with patch.object(m,'start'),patch('sentinel_forge.persistent_model.request.urlopen',return_value=response):
                if content=='</think>':
                    with self.assertRaises(EnrollmentError):m.respond('question','context')
                else:self.assertEqual('Answer',m.respond('question','context'))


class SmokeHarnessTests(unittest.TestCase):
    def harness(self):
        import importlib.util
        path=Path(__file__).resolve().parents[1]/'scripts/forge_llama_smoke.py'
        spec=importlib.util.spec_from_file_location('forge_smoke',path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        return module

    def test_opt_in_and_missing_model(self):
        from types import SimpleNamespace
        h=self.harness()
        self.assertEqual(77,h.run(SimpleNamespace(run=False))[1])
        self.assertEqual(77,h.run(SimpleNamespace(run=True,executable=Path('/nonexistent'),model=Path('/nonexistent')))[1])

    def test_inference_failure_and_interrupt_always_close(self):
        from types import SimpleNamespace
        h=self.harness()
        path=Path(__file__).resolve()
        args=SimpleNamespace(run=True,executable=path,model=path)
        for exception in (RuntimeError('private message'),KeyboardInterrupt()):
            sock=Mock();sock.getsockname.return_value=('127.0.0.1',19999);sock.connect_ex.return_value=111
            context=Mock();context.__enter__=Mock(return_value=sock);context.__exit__=Mock(return_value=False)
            model=Mock();model.respond.side_effect=exception;model._process=None;model.last_exit_code=-15;model.diagnostics={}
            with patch.object(h.os,'access',return_value=True),patch.object(h.socket,'socket',return_value=context),patch.object(h,'PersistentLocalModel',return_value=model),patch.object(h.signal,'signal'),patch.object(h.signal,'setitimer'):
                result,code=h.run(args)
            self.assertEqual(1,code);self.assertEqual('failure',result['status'])
            self.assertNotIn('private message',str(result));model.close.assert_called_once()

    def test_socket_unavailable_is_not_inference_failure(self):
        from types import SimpleNamespace
        h=self.harness();path=Path(__file__).resolve()
        with patch.object(h.os,'access',return_value=True),patch.object(h.socket,'socket',side_effect=PermissionError):
            result,code=h.run(SimpleNamespace(run=True,executable=path,model=path))
        self.assertEqual(77,code);self.assertFalse(result['child_started'])
