import dataclasses,tempfile,unittest
from pathlib import Path
from sentinel_forge.assistant_independence import *
from sentinel_forge.courier_ack import build_ack
from sentinel_forge.enrollment import EnrollmentError
from sentinel_forge.evidence import EvidenceError,EvidenceJournal
from sentinel_forge.evidence_anchor import EvidenceHead,build_evidence_head,verify_against_head
from sentinel_forge.state_backup import *
class PreCampaignHardening(unittest.TestCase):
 def inv(self):return build_inventory(forge_identity="forge",collector_method="test",categories_observed=list(REQUIRED_CATEGORIES),findings=[])
 def test_attestation_truthy_strings_rejected(self):
  inv=self.inv()
  for a,b in (("false",True),(True,"false"),(1,True),(True,1),(None,True)):
   with self.subTest(a=a,b=b):
    with self.assertRaises(EnrollmentError):build_attestation(inv,verifier_identity="v",verification_scope="host",host_observed=a,development_access_removed=b)
 def test_evidence_head_type_confusion_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   e=EvidenceJournal(Path(td)/"e");e.append(correlation_id="c");h=build_evidence_head(e,journal_identity="forge")
   for bad in (dataclasses.replace(h,sequence=True),dataclasses.replace(h,sequence=[]),dataclasses.replace(h,event_hash=None),dataclasses.replace(h,journal_identity="")):
    with self.subTest(bad=bad):
     with self.assertRaises(EvidenceError):verify_against_head(e,bad)
 def test_backup_duplicate_rows_rejected_even_with_recomputed_manifest_impossible_through_verifier(self):
  with tempfile.TemporaryDirectory() as td:
   r=Path(td);files={}
   for n in ALLOWED:p=r/n;p.write_bytes(n.encode());files[n]=p
   m=build_state_backup_manifest(relationship_id="rel",files=files)
   bad=dataclasses.replace(m,files=(m.files[0],m.files[0],m.files[2],m.files[3]))
   with self.assertRaises(EnrollmentError):verify_restored_state(bad,expected_relationship_id="rel",files=files)
 def test_ack_nonstring_disposition_rejected_cleanly(self):
  class C:
   relationship_id="r";session_id="s";session_generation=1;credential_generation=1;context_digest="d"
  for bad in ([],{},1,True,None):
   with self.subTest(bad=bad):
    with self.assertRaises(EnrollmentError):build_ack(C(),sequence=1,operation="o",artifact_identity="a",disposition=bad,reason="r")
