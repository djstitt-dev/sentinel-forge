import tempfile,unittest
from pathlib import Path
from sentinel_forge.courier_queue import CourierQueue
from sentinel_forge.enrollment import EnrollmentError
class QueueTerminalExhaustionTests(unittest.TestCase):
 def q(self,td):q=CourierQueue(Path(td)/"q");i=q.enqueue(relationship_id="r",artifact_identity="a",operation="d",payload_identity="p");return q,i
 def ack(self,q,i):q.transition(i,expected="QUEUED",new="PREPARED",sequence=1);q.transition(i,expected="PREPARED",new="IN_FLIGHT",sequence=1);q.transition(i,expected="IN_FLIGHT",new="ACKNOWLEDGED",sequence=1,acknowledgement="ack")
 def reject(self,q,i):q.transition(i,expected="QUEUED",new="PREPARED",sequence=1);q.transition(i,expected="PREPARED",new="IN_FLIGHT",sequence=1);q.transition(i,expected="IN_FLIGHT",new="REJECTED",sequence=1)
 def cancel(self,q,i):q.transition(i,expected="QUEUED",new="CANCELLED")
 def attempt(self,maker,new):
  with tempfile.TemporaryDirectory() as td:
   q,i=self.q(td);maker(q,i)
   with self.assertRaises(EnrollmentError):q.transition(i,expected=q.get(i)["state"],new=new,sequence=1,acknowledgement="ack")
 def test_ack_to_prepared(self):self.attempt(self.ack,"PREPARED")
 def test_ack_to_inflight(self):self.attempt(self.ack,"IN_FLIGHT")
 def test_ack_to_rejected(self):self.attempt(self.ack,"REJECTED")
 def test_rejected_to_prepared(self):self.attempt(self.reject,"PREPARED")
 def test_rejected_to_inflight(self):self.attempt(self.reject,"IN_FLIGHT")
 def test_rejected_to_ack(self):self.attempt(self.reject,"ACKNOWLEDGED")
 def test_cancelled_to_prepared(self):self.attempt(self.cancel,"PREPARED")
 def test_cancelled_to_inflight(self):self.attempt(self.cancel,"IN_FLIGHT")
 def test_cancelled_to_ack(self):self.attempt(self.cancel,"ACKNOWLEDGED")
