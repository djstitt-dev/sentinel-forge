import dataclasses,tempfile,unittest
from pathlib import Path
from sentinel_forge.evidence import EvidenceError,EvidenceJournal
from sentinel_forge.evidence_anchor import build_evidence_head,verify_against_head
class EvidenceAnchorTests(unittest.TestCase):
 def test_checkpoint_verifies_same_journal(self):
  with tempfile.TemporaryDirectory() as td:e=EvidenceJournal(Path(td)/"e");e.append(correlation_id="1");h=build_evidence_head(e,journal_identity="forge");verify_against_head(e,h)
 def test_append_after_checkpoint_still_verifies_history(self):
  with tempfile.TemporaryDirectory() as td:e=EvidenceJournal(Path(td)/"e");e.append(correlation_id="1");h=build_evidence_head(e,journal_identity="forge");e.append(correlation_id="2");verify_against_head(e,h)
 def test_tail_rollback_detected_against_checkpoint(self):
  with tempfile.TemporaryDirectory() as td:
   e=EvidenceJournal(Path(td)/"e");e.append(correlation_id="1");e.append(correlation_id="2");h=build_evidence_head(e,journal_identity="forge");lines=e.path.read_text().splitlines();e.path.write_text(lines[0]+"\n")
   with self.assertRaisesRegex(EvidenceError,"rollback"):verify_against_head(e,h)
 def test_checkpoint_tamper_detected(self):
  with tempfile.TemporaryDirectory() as td:
   e=EvidenceJournal(Path(td)/"e");e.append(correlation_id="1");h=build_evidence_head(e,journal_identity="forge")
   with self.assertRaises(EvidenceError):verify_against_head(e,dataclasses.replace(h,sequence=0))
