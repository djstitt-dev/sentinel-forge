import tempfile,unittest
from pathlib import Path
from sentinel_forge.courier_queue import CourierQueue
from sentinel_forge.courier_recovery import classify_delivery_recovery
from sentinel_forge.delivery_journal import DeliveryJournal

class CourierRecoveryTests(unittest.TestCase):
 def setUp(self):self.td=tempfile.TemporaryDirectory();r=Path(self.td.name);self.q=CourierQueue(r/"q");self.j=DeliveryJournal(r/"j")
 def tearDown(self):self.td.cleanup()
 def seed(self):
  i=self.q.enqueue(relationship_id="r",artifact_identity="a",operation="d",payload_identity="p")
  self.j.append(item_id=i,relationship_id="r",delivery_sequence=None,prior_state=None,state="QUEUED",artifact_identity="a",reason="q");return i
 def test_absent_no_action(self):self.assertEqual("NO_ACTION",classify_delivery_recovery(self.q,self.j,"x").classification)
 def test_queued_safe_only_to_revalidate(self):self.assertEqual("SAFE_TO_REVALIDATE",classify_delivery_recovery(self.q,self.j,self.seed()).classification)
 def test_prepared_requires_operator(self):
  i=self.seed();self.q.transition(i,expected="QUEUED",new="PREPARED",sequence=1);self.j.append(item_id=i,relationship_id="r",delivery_sequence=1,prior_state="QUEUED",state="PREPARED",artifact_identity="a",reason="p")
  self.assertEqual("OPERATOR_REQUIRED",classify_delivery_recovery(self.q,self.j,i).classification)
 def test_inflight_requires_reconciliation(self):
  i=self.seed();self.q.transition(i,expected="QUEUED",new="PREPARED",sequence=1);self.j.append(item_id=i,relationship_id="r",delivery_sequence=1,prior_state="QUEUED",state="PREPARED",artifact_identity="a",reason="p");self.q.transition(i,expected="PREPARED",new="IN_FLIGHT",sequence=1);self.j.append(item_id=i,relationship_id="r",delivery_sequence=1,prior_state="PREPARED",state="IN_FLIGHT",artifact_identity="a",reason="i")
  self.assertEqual("RECONCILIATION_REQUIRED",classify_delivery_recovery(self.q,self.j,i).classification)
 def test_disagreement_requires_reconciliation(self):
  i=self.seed();self.q.transition(i,expected="QUEUED",new="PREPARED",sequence=1)
  self.assertEqual("RECONCILIATION_REQUIRED",classify_delivery_recovery(self.q,self.j,i).classification)
 def test_corrupt_journal_requires_operator(self):
  i=self.seed();self.j.path.write_text("garbage")
  self.assertEqual("OPERATOR_REQUIRED",classify_delivery_recovery(self.q,self.j,i).classification)
