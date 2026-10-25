import dataclasses,tempfile,unittest
from pathlib import Path
from sentinel_forge.courier_manifest import build_manifest,verify_manifest
from sentinel_forge.delivery_journal import DeliveryJournal
from sentinel_forge.enrollment import EnrollmentError

class ManifestReceiptTests(unittest.TestCase):
 def setUp(self):
  self.m=build_manifest(relationship_id="rel",sender_identity="forge",recipient_identity="reaper",operation="deliver",classification="CONTROLLED",artifact_identity="sha256:a",payload_identity="sha256:a",policy_reference="p")
 def test_manifest_exact_binding(self):verify_manifest(self.m,recipient_identity="reaper",classification="CONTROLLED",operation="deliver")
 def test_manifest_substitution_rejected(self):
  with self.assertRaises(EnrollmentError):verify_manifest(dataclasses.replace(self.m,recipient_identity="scribe"),recipient_identity="reaper")
 def test_receipt_chain_preserves_same_artifact(self):
  with tempfile.TemporaryDirectory() as td:
   j=DeliveryJournal(Path(td)/"j")
   states=[(None,"QUEUED",None),("QUEUED","PREPARED",1),("PREPARED","IN_FLIGHT",1),("IN_FLIGHT","ACKNOWLEDGED",1)]
   for prior,state,seq in states:j.append(item_id="q",relationship_id="rel",delivery_sequence=seq,prior_state=prior,state=state,artifact_identity=self.m.artifact_identity,reason=state)
   events=j.verify();self.assertEqual(4,len(events));self.assertEqual({self.m.artifact_identity},{e.artifact_identity for e in events})
 def test_receipt_chain_substitution_breaks_logical_identity(self):
  with tempfile.TemporaryDirectory() as td:
   j=DeliveryJournal(Path(td)/"j");j.append(item_id="q",relationship_id="rel",delivery_sequence=None,prior_state=None,state="QUEUED",artifact_identity="a",reason="q")
   with self.assertRaisesRegex(EnrollmentError,"logical identity changed"):
    j.append(item_id="q",relationship_id="rel",delivery_sequence=1,prior_state="QUEUED",state="PREPARED",artifact_identity="b",reason="p")
