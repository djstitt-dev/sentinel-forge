import dataclasses,json,tempfile,unittest
from pathlib import Path
from sentinel_forge.enrollment import EnrollmentError
from sentinel_forge.evidence import EvidenceJournal,EvidenceError
from sentinel_forge.evidence_anchor import build_evidence_head,verify_against_head
from sentinel_forge.state_backup import ALLOWED,build_state_backup_manifest,verify_restored_state
class EvidenceBackupAssault(unittest.TestCase):
 def test_100_evidence_prefix_rollbacks_detected(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"e";e=EvidenceJournal(p)
   for i in range(100):e.append(correlation_id=str(i))
   h=build_evidence_head(e,journal_identity="forge");lines=p.read_text().splitlines()
   for n in range(100):
    with self.subTest(n=n):
     p.write_text("\n".join(lines[:n])+("\n" if n else ""))
     with self.assertRaises(EvidenceError):verify_against_head(e,h)
     p.write_text("\n".join(lines)+"\n")
 def test_100_event_line_mutations_detected(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"e";e=EvidenceJournal(p)
   for i in range(10):e.append(correlation_id=str(i))
   lines=p.read_text().splitlines()
   for seed in range(100):
    with self.subTest(seed=seed):
     row=seed%len(lines);d=json.loads(lines[row]);d["reason"]=str(d["reason"])+"x";m=list(lines);m[row]=json.dumps(d);p.write_text("\n".join(m)+"\n")
     with self.assertRaises(EvidenceError):e.verify()
     p.write_text("\n".join(lines)+"\n")
 def test_backup_each_file_mutation_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   r=Path(td);files={}
   for n in ALLOWED:p=r/n;p.write_bytes(("data-"+n).encode());files[n]=p
   m=build_state_backup_manifest(relationship_id="rel",files=files)
   for n in ALLOWED:
    with self.subTest(n=n):
     original=files[n].read_bytes();files[n].write_bytes(original+b"x")
     with self.assertRaises(EnrollmentError):verify_restored_state(m,expected_relationship_id="rel",files=files)
     files[n].write_bytes(original)
 def test_backup_relationship_substitution_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   r=Path(td);files={n:r/n for n in ALLOWED}
   for n,p in files.items():p.write_bytes(n.encode())
   m=build_state_backup_manifest(relationship_id="rel",files=files)
   with self.assertRaises(EnrollmentError):verify_restored_state(m,expected_relationship_id="other",files=files)
 def test_backup_manifest_field_mutations_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   r=Path(td);files={n:r/n for n in ALLOWED}
   for n,p in files.items():p.write_bytes(n.encode())
   m=build_state_backup_manifest(relationship_id="rel",files=files)
   for bad in (dataclasses.replace(m,format="x"),dataclasses.replace(m,relationship_id="x"),dataclasses.replace(m,manifest_digest="sha256:"+"0"*64)):
    with self.subTest(bad=bad):
     with self.assertRaises(EnrollmentError):verify_restored_state(bad,expected_relationship_id="rel",files=files)
