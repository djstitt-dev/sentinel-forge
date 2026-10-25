import tempfile,unittest
from pathlib import Path
from sentinel_forge.courier_queue import CourierQueue
from sentinel_forge.courier_recovery import classify_delivery_recovery
from sentinel_forge.delivery_journal import DeliveryJournal
class RestartMatrixTests(unittest.TestCase):
 def setup_pair(self,td):
  r=Path(td);q=CourierQueue(r/"q");j=DeliveryJournal(r/"j");i=q.enqueue(relationship_id="r",artifact_identity="a",operation="d",payload_identity="p");j.append(item_id=i,relationship_id="r",delivery_sequence=None,prior_state=None,state="QUEUED",artifact_identity="a",reason="q");return r,q,j,i
 def advance(self,q,j,i,a,b,seq=1,ack=None):
  q.transition(i,expected=a,new=b,sequence=seq,acknowledgement=ack);j.append(item_id=i,relationship_id="r",delivery_sequence=None if b=="CANCELLED" else seq,prior_state=a,state=b,artifact_identity="a",reason=b)
 def decision_after_restart(self,r,i):return classify_delivery_recovery(CourierQueue(r/"q"),DeliveryJournal(r/"j"),i).classification
 def test_queued_restart_safe_revalidate(self):
  with tempfile.TemporaryDirectory() as td:r,q,j,i=self.setup_pair(td);self.assertEqual("SAFE_TO_REVALIDATE",self.decision_after_restart(r,i))
 def test_prepared_restart_operator(self):
  with tempfile.TemporaryDirectory() as td:r,q,j,i=self.setup_pair(td);self.advance(q,j,i,"QUEUED","PREPARED");self.assertEqual("OPERATOR_REQUIRED",self.decision_after_restart(r,i))
 def test_inflight_restart_reconcile(self):
  with tempfile.TemporaryDirectory() as td:r,q,j,i=self.setup_pair(td);self.advance(q,j,i,"QUEUED","PREPARED");self.advance(q,j,i,"PREPARED","IN_FLIGHT");self.assertEqual("RECONCILIATION_REQUIRED",self.decision_after_restart(r,i))
 def test_unknown_restart_reconcile(self):
  with tempfile.TemporaryDirectory() as td:r,q,j,i=self.setup_pair(td);self.advance(q,j,i,"QUEUED","PREPARED");self.advance(q,j,i,"PREPARED","IN_FLIGHT");self.advance(q,j,i,"IN_FLIGHT","OUTCOME_UNKNOWN");self.assertEqual("RECONCILIATION_REQUIRED",self.decision_after_restart(r,i))
 def test_ack_restart_terminal(self):
  with tempfile.TemporaryDirectory() as td:r,q,j,i=self.setup_pair(td);self.advance(q,j,i,"QUEUED","PREPARED");self.advance(q,j,i,"PREPARED","IN_FLIGHT");self.advance(q,j,i,"IN_FLIGHT","ACKNOWLEDGED",ack="ack");self.assertEqual("TERMINAL",self.decision_after_restart(r,i))
 def test_reject_restart_terminal(self):
  with tempfile.TemporaryDirectory() as td:r,q,j,i=self.setup_pair(td);self.advance(q,j,i,"QUEUED","PREPARED");self.advance(q,j,i,"PREPARED","IN_FLIGHT");self.advance(q,j,i,"IN_FLIGHT","REJECTED");self.assertEqual("TERMINAL",self.decision_after_restart(r,i))
 def test_cancel_restart_terminal(self):
  with tempfile.TemporaryDirectory() as td:r,q,j,i=self.setup_pair(td);self.advance(q,j,i,"QUEUED","CANCELLED",seq=None);self.assertEqual("TERMINAL",self.decision_after_restart(r,i))
 def test_missing_queue_restart_reconcile(self):
  with tempfile.TemporaryDirectory() as td:r,q,j,i=self.setup_pair(td);(r/"q").write_text("{}");self.assertEqual("RECONCILIATION_REQUIRED",self.decision_after_restart(r,i))
 def test_missing_journal_restart_reconcile(self):
  with tempfile.TemporaryDirectory() as td:r,q,j,i=self.setup_pair(td);(r/"j").write_text("");self.assertEqual("RECONCILIATION_REQUIRED",self.decision_after_restart(r,i))
