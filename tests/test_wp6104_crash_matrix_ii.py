import json,tempfile,unittest
from pathlib import Path
from sentinel_forge.courier_queue import CourierQueue
from sentinel_forge.courier_recovery import classify_delivery_recovery
from sentinel_forge.delivery_journal import DeliveryJournal
from sentinel_forge.enrollment import EnrollmentError
class CrashMatrixII(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();r=Path(self.t.name);self.q=CourierQueue(r/"q");self.j=DeliveryJournal(r/"j");self.i=self.q.enqueue(relationship_id="r",artifact_identity="a",operation="d",payload_identity="p");self.j.append(item_id=self.i,relationship_id="r",delivery_sequence=None,prior_state=None,state="QUEUED",artifact_identity="a",reason="q")
 def tearDown(self):self.t.cleanup()
 def step(self,a,b,seq=1,ack=None):
  self.q.transition(self.i,expected=a,new=b,sequence=seq,acknowledgement=ack);self.j.append(item_id=self.i,relationship_id="r",delivery_sequence=None if b=="CANCELLED" else seq,prior_state=a,state=b,artifact_identity="a",reason=b)
 def inflight(self):self.step("QUEUED","PREPARED");self.step("PREPARED","IN_FLIGHT")
 def test_queue_ack_ahead_requires_reconciliation(self):
  self.inflight();self.q.transition(self.i,expected="IN_FLIGHT",new="ACKNOWLEDGED",sequence=1,acknowledgement="ack");self.assertEqual("RECONCILIATION_REQUIRED",classify_delivery_recovery(self.q,self.j,self.i).classification)
 def test_journal_ack_ahead_requires_reconciliation(self):
  self.inflight();self.j.append(item_id=self.i,relationship_id="r",delivery_sequence=1,prior_state="IN_FLIGHT",state="ACKNOWLEDGED",artifact_identity="a",reason="ack");self.assertEqual("RECONCILIATION_REQUIRED",classify_delivery_recovery(self.q,self.j,self.i).classification)
 def test_queue_unknown_ahead_requires_reconciliation(self):
  self.inflight();self.q.transition(self.i,expected="IN_FLIGHT",new="OUTCOME_UNKNOWN",sequence=1);self.assertEqual("RECONCILIATION_REQUIRED",classify_delivery_recovery(self.q,self.j,self.i).classification)
 def test_journal_unknown_ahead_requires_reconciliation(self):
  self.inflight();self.j.append(item_id=self.i,relationship_id="r",delivery_sequence=1,prior_state="IN_FLIGHT",state="OUTCOME_UNKNOWN",artifact_identity="a",reason="u");self.assertEqual("RECONCILIATION_REQUIRED",classify_delivery_recovery(self.q,self.j,self.i).classification)
 def test_consistent_ack_terminal(self):
  self.inflight();self.step("IN_FLIGHT","ACKNOWLEDGED",ack="ack");self.assertEqual("TERMINAL",classify_delivery_recovery(self.q,self.j,self.i).classification)
 def test_consistent_reject_terminal(self):
  self.inflight();self.step("IN_FLIGHT","REJECTED");self.assertEqual("TERMINAL",classify_delivery_recovery(self.q,self.j,self.i).classification)
 def test_consistent_unknown_reconciliation(self):
  self.inflight();self.step("IN_FLIGHT","OUTCOME_UNKNOWN");self.assertEqual("RECONCILIATION_REQUIRED",classify_delivery_recovery(self.q,self.j,self.i).classification)
 def test_corrupt_queue_operator_required(self):
  self.q.path.write_text("{bad");self.assertEqual("OPERATOR_REQUIRED",classify_delivery_recovery(self.q,self.j,self.i).classification)
 def test_corrupt_journal_operator_required(self):
  self.j.path.write_text("{bad");self.assertEqual("OPERATOR_REQUIRED",classify_delivery_recovery(self.q,self.j,self.i).classification)
 def test_journal_sequence_change_rejected(self):
  self.step("QUEUED","PREPARED",1)
  with self.assertRaisesRegex(EnrollmentError,"sequence changed"):self.j.append(item_id=self.i,relationship_id="r",delivery_sequence=2,prior_state="PREPARED",state="IN_FLIGHT",artifact_identity="a",reason="bad")
 def test_journal_bool_sequence_rejected(self):
  with self.assertRaises(EnrollmentError):self.j.append(item_id=self.i,relationship_id="r",delivery_sequence=True,prior_state="QUEUED",state="PREPARED",artifact_identity="a",reason="bad")
