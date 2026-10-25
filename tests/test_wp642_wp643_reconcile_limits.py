import tempfile,unittest
from pathlib import Path
from sentinel_forge.courier_ack import build_ack
from sentinel_forge.courier_limits import CourierLimits,enforce_backpressure,enforce_payload
from sentinel_forge.courier_queue import CourierQueue
from sentinel_forge.courier_reconcile import assess_delivery,reconcile_with_ack
from sentinel_forge.enrollment import EnrollmentError
from sentinel_forge.transport_contract import TransportMessageContext

def ctx():
 return TransportMessageContext("sentinel-transport-message-context-v1","rel","session:x",1,1,"key","bind","header","ctx")

class ReconcileLimitTests(unittest.TestCase):
 def setUp(self):
  self.td=tempfile.TemporaryDirectory();self.q=CourierQueue(Path(self.td.name)/"q.json")
  self.i=self.q.enqueue(relationship_id="rel",artifact_identity="a",operation="deliver",payload_identity="p")
  self.q.transition(self.i,expected="QUEUED",new="PREPARED",sequence=1)
  self.q.transition(self.i,expected="PREPARED",new="IN_FLIGHT",sequence=1)
 def tearDown(self):self.td.cleanup()
 def test_inflight_requires_reconciliation(self):self.assertEqual("RECONCILIATION_REQUIRED",assess_delivery(self.q,self.i).conclusion)
 def test_unknown_never_means_retry(self):
  self.q.transition(self.i,expected="IN_FLIGHT",new="OUTCOME_UNKNOWN",sequence=1)
  self.assertEqual("RECONCILIATION_REQUIRED",assess_delivery(self.q,self.i).conclusion)
 def test_bound_accept_ack_closes(self):
  a=build_ack(ctx(),sequence=1,operation="deliver",artifact_identity="a",disposition="ACCEPTED",reason="stored")
  self.assertEqual("ACKNOWLEDGED",reconcile_with_ack(self.q,self.i,a,ctx(),operation="deliver",artifact_identity="a",sequence=1))
 def test_wrong_ack_cannot_close(self):
  a=build_ack(ctx(),sequence=2,operation="deliver",artifact_identity="a",disposition="ACCEPTED",reason="stored")
  with self.assertRaises(EnrollmentError):reconcile_with_ack(self.q,self.i,a,ctx(),operation="deliver",artifact_identity="a",sequence=1)
 def test_payload_limit(self):
  enforce_payload(b"x",CourierLimits(max_payload_bytes=1))
  with self.assertRaises(EnrollmentError):enforce_payload(b"xx",CourierLimits(max_payload_bytes=1))
 def test_backpressure(self):
  q=CourierQueue(Path(self.td.name)/"q2.json")
  q.enqueue(relationship_id="r",artifact_identity="a",operation="d",payload_identity="p")
  with self.assertRaisesRegex(EnrollmentError,"backpressure"):enforce_backpressure(q,"r",CourierLimits(max_pending_per_relationship=1))
