import tempfile,unittest
from pathlib import Path
from sentinel_forge.courier_queue import CourierQueue
from sentinel_forge.delivery_consistency import require_delivery_consistent
from sentinel_forge.delivery_journal import DeliveryJournal
from sentinel_forge.enrollment import EnrollmentError

class DeliveryJournalTests(unittest.TestCase):
 def setUp(self):
  self.td=tempfile.TemporaryDirectory();r=Path(self.td.name);self.q=CourierQueue(r/"q");self.j=DeliveryJournal(r/"j")
  self.i=self.q.enqueue(relationship_id="rel",artifact_identity="a",operation="deliver",payload_identity="p")
  self.j.append(item_id=self.i,relationship_id="rel",delivery_sequence=None,prior_state=None,state="QUEUED",artifact_identity="a",reason="enqueued")
 def tearDown(self):self.td.cleanup()
 def test_consistent_genesis(self):require_delivery_consistent(self.q,self.j,self.i)
 def test_transition_chain(self):
  self.q.transition(self.i,expected="QUEUED",new="PREPARED",sequence=1);self.j.append(item_id=self.i,relationship_id="rel",delivery_sequence=1,prior_state="QUEUED",state="PREPARED",artifact_identity="a",reason="prepared")
  require_delivery_consistent(self.q,self.j,self.i)
 def test_queue_ahead_fails(self):
  self.q.transition(self.i,expected="QUEUED",new="PREPARED",sequence=1)
  with self.assertRaisesRegex(EnrollmentError,"state disagreement"):require_delivery_consistent(self.q,self.j,self.i)
 def test_journal_ahead_fails(self):
  self.j.append(item_id=self.i,relationship_id="rel",delivery_sequence=1,prior_state="QUEUED",state="PREPARED",artifact_identity="a",reason="prepared")
  with self.assertRaises(EnrollmentError):require_delivery_consistent(self.q,self.j,self.i)
 def test_tamper_detected(self):
  data=self.j.path.read_text().replace('"reason":"enqueued"','"reason":"evil"');self.j.path.write_text(data)
  with self.assertRaisesRegex(EnrollmentError,"integrity"):self.j.verify()
 def test_illegal_transition_rejected(self):
  with self.assertRaisesRegex(EnrollmentError,"transition invalid"):self.j.append(item_id=self.i,relationship_id="rel",delivery_sequence=1,prior_state="QUEUED",state="ACKNOWLEDGED",artifact_identity="a",reason="bad")
