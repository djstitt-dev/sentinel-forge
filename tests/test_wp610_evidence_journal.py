import json
import multiprocessing
from pathlib import Path
import tempfile
import unittest
from sentinel_forge.evidence import EvidenceError, EvidenceJournal, REDACTED, UNKNOWN



def _evidence_append_worker(path,index,queue):
 try:
  event=EvidenceJournal(Path(path)).append(
   correlation_id=f"c{index}",actor="forge",target="courier",authorization_reference=f"a{index}",
   input_identity=f"artifact{index}",output_identity=None,outcome="PROPOSED",reason="concurrent",
   source_context="forge",collector_method="local-reference",timestamp=None,time_uncertainty="UNKNOWN")
  queue.put(("OK",event.sequence,event.correlation_id))
 except Exception as exc:
  queue.put((type(exc).__name__,str(exc)))

class EvidenceJournalTests(unittest.TestCase):
    def setUp(self):
        self.td=tempfile.TemporaryDirectory(); self.path=Path(self.td.name)/"journal.jsonl"
        self.j=EvidenceJournal(self.path)
    def tearDown(self): self.td.cleanup()
    def event(self,**extra):
        d=dict(correlation_id="c1",actor="forge",target="courier",authorization_reference="a1",
          input_identity="artifact1",output_identity=None,outcome="PROPOSED",reason="validated",
          source_context="forge",collector_method="local-reference",timestamp=None,time_uncertainty="UNKNOWN")
        d.update(extra); return d
    def test_append_and_verify_chain(self):
        a=self.j.append(**self.event()); b=self.j.append(**self.event(outcome="REJECTED"))
        events=self.j.verify(); self.assertEqual([a,b],events); self.assertEqual(a.event_hash,b.previous_hash)
    def test_unknowns_are_explicit_not_fabricated(self):
        e=self.j.append(**self.event())
        self.assertEqual(UNKNOWN,e.output_identity); self.assertEqual(UNKNOWN,e.timestamp)
    def test_sensitive_named_fields_are_rejected(self):
        with self.assertRaises(EvidenceError): self.j.append(**self.event(token="nope"))
    def test_obvious_secret_payload_is_redacted(self):
        e=self.j.append(**self.event(reason="Bearer abc123"))
        self.assertEqual(REDACTED,e.reason)
    def test_modified_record_is_detected(self):
        self.j.append(**self.event())
        raw=json.loads(self.path.read_text()); raw["outcome"]="TRANSFERRED"
        self.path.write_text(json.dumps(raw)+"\n")
        with self.assertRaises(EvidenceError): self.j.verify()
    def test_deleted_middle_record_is_detected(self):
        for x in range(3): self.j.append(**self.event(outcome=str(x)))
        lines=self.path.read_text().splitlines(); self.path.write_text(lines[0]+"\n"+lines[2]+"\n")
        with self.assertRaises(EvidenceError): self.j.verify()
    def test_reordered_records_are_detected(self):
        self.j.append(**self.event(outcome="1")); self.j.append(**self.event(outcome="2"))
        lines=self.path.read_text().splitlines(); self.path.write_text("\n".join(reversed(lines))+"\n")
        with self.assertRaises(EvidenceError): self.j.verify()
    def test_malformed_record_is_detected(self):
        self.path.write_text("{bad\n")
        with self.assertRaises(EvidenceError): self.j.verify()
    def test_log_write_does_not_expose_authority_methods(self):
        self.j.append(**self.event())
        self.assertFalse(hasattr(self.j,"authorize")); self.assertFalse(hasattr(self.j,"release"))
        self.assertFalse(hasattr(self.j,"deploy"))

if __name__=="__main__": unittest.main()


class EvidenceJournalConcurrencyTests(unittest.TestCase):
    def test_multiprocess_append_preserves_one_global_chain(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"journal.jsonl";q=multiprocessing.Queue()
            ps=[multiprocessing.Process(target=_evidence_append_worker,args=(str(path),i,q)) for i in range(8)]
            for proc in ps:proc.start()
            for proc in ps:proc.join(5)
            self.assertTrue(all(not proc.is_alive() and proc.exitcode==0 for proc in ps),
                            [(proc.pid,proc.exitcode) for proc in ps])
            results=[q.get(timeout=2) for _ in ps]
            self.assertTrue(all(x[0]=="OK" for x in results),results)
            self.assertEqual(list(range(1,9)),sorted(x[1] for x in results))
            events=EvidenceJournal(path).verify()
            self.assertEqual(8,len(events));self.assertEqual(list(range(1,9)),[e.sequence for e in events])
