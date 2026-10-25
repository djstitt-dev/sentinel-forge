import tempfile,unittest
from pathlib import Path
from sentinel_forge.courier_queue import CourierQueue
from sentinel_forge.courier_recovery import classify_delivery_recovery
from sentinel_forge.delivery_journal import DeliveryJournal

class CrashPointTests(unittest.TestCase):
 def setUp(self):
  self.td=tempfile.TemporaryDirectory();r=Path(self.td.name);self.q=CourierQueue(r/"q");self.j=DeliveryJournal(r/"j")
  self.i=self.q.enqueue(relationship_id="r",artifact_identity="a",operation="d",payload_identity="p")
  self.j.append(item_id=self.i,relationship_id="r",delivery_sequence=None,prior_state=None,state="QUEUED",artifact_identity="a",reason="q")
 def tearDown(self):self.td.cleanup()
 def journal(self,a,b,seq):self.j.append(item_id=self.i,relationship_id="r",delivery_sequence=seq,prior_state=a,state=b,artifact_identity="a",reason=b)
 def test_crash_after_queue_prepare_before_journal(self):
  self.q.transition(self.i,expected="QUEUED",new="PREPARED",sequence=1)
  self.assertEqual("RECONCILIATION_REQUIRED",classify_delivery_recovery(self.q,self.j,self.i).classification)
 def test_crash_after_journal_prepare_before_queue(self):
  self.journal("QUEUED","PREPARED",1)
  self.assertEqual("RECONCILIATION_REQUIRED",classify_delivery_recovery(self.q,self.j,self.i).classification)
 def test_crash_after_queue_inflight_before_journal(self):
  self.q.transition(self.i,expected="QUEUED",new="PREPARED",sequence=1);self.journal("QUEUED","PREPARED",1)
  self.q.transition(self.i,expected="PREPARED",new="IN_FLIGHT",sequence=1)
  self.assertEqual("RECONCILIATION_REQUIRED",classify_delivery_recovery(self.q,self.j,self.i).classification)
 def test_crash_after_journal_inflight_before_queue(self):
  self.q.transition(self.i,expected="QUEUED",new="PREPARED",sequence=1);self.journal("QUEUED","PREPARED",1);self.journal("PREPARED","IN_FLIGHT",1)
  self.assertEqual("RECONCILIATION_REQUIRED",classify_delivery_recovery(self.q,self.j,self.i).classification)
 def test_consistent_inflight_still_reconciliation(self):
  self.q.transition(self.i,expected="QUEUED",new="PREPARED",sequence=1);self.journal("QUEUED","PREPARED",1);self.q.transition(self.i,expected="PREPARED",new="IN_FLIGHT",sequence=1);self.journal("PREPARED","IN_FLIGHT",1)
  self.assertEqual("RECONCILIATION_REQUIRED",classify_delivery_recovery(self.q,self.j,self.i).classification)
