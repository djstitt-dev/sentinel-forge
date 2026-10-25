import multiprocessing,tempfile,unittest
from pathlib import Path
from sentinel_forge.courier_queue import CourierQueue
from sentinel_forge.enrollment import EnrollmentError

def _enqueue(path,q):
 try:q.put(("ok",CourierQueue(Path(path)).enqueue(relationship_id="rel",artifact_identity="a",operation="deliver",payload_identity="p")))
 except Exception as exc:q.put(("err",type(exc).__name__))

class CourierQueueTests(unittest.TestCase):
 def setUp(self):
  self.td=tempfile.TemporaryDirectory();self.path=Path(self.td.name)/"q.json";self.q=CourierQueue(self.path)
 def tearDown(self):self.td.cleanup()
 def add(self):
  return self.q.enqueue(relationship_id="rel",artifact_identity="a",operation="deliver",payload_identity="p")
 def test_enqueue_is_deterministic(self):
  self.assertEqual(self.add(),self.add())
 def test_delivery_lifecycle(self):
  i=self.add();self.q.transition(i,expected="QUEUED",new="PREPARED",sequence=1)
  self.q.transition(i,expected="PREPARED",new="IN_FLIGHT",sequence=1)
  self.q.transition(i,expected="IN_FLIGHT",new="ACKNOWLEDGED",sequence=1,acknowledgement="ack:1")
  self.assertEqual("ACKNOWLEDGED",self.q.get(i)["state"]);self.assertEqual([],self.q.pending("rel"))
 def test_unknown_outcome_can_only_reconcile_final(self):
  i=self.add();self.q.transition(i,expected="QUEUED",new="PREPARED",sequence=1)
  self.q.transition(i,expected="PREPARED",new="IN_FLIGHT",sequence=1)
  self.q.transition(i,expected="IN_FLIGHT",new="OUTCOME_UNKNOWN",sequence=1)
  with self.assertRaises(EnrollmentError):self.q.transition(i,expected="OUTCOME_UNKNOWN",new="IN_FLIGHT",sequence=1)
  self.q.transition(i,expected="OUTCOME_UNKNOWN",new="REJECTED",sequence=1)
 def test_sequence_is_immutable(self):
  i=self.add();self.q.transition(i,expected="QUEUED",new="PREPARED",sequence=1)
  with self.assertRaises(EnrollmentError):self.q.transition(i,expected="PREPARED",new="IN_FLIGHT",sequence=2)
 def test_ack_required(self):
  i=self.add();self.q.transition(i,expected="QUEUED",new="PREPARED",sequence=1)
  self.q.transition(i,expected="PREPARED",new="IN_FLIGHT",sequence=1)
  with self.assertRaisesRegex(EnrollmentError,"acknowledgement"):self.q.transition(i,expected="IN_FLIGHT",new="ACKNOWLEDGED",sequence=1)
 def test_malformed_state_fails(self):
  self.path.write_text('{"x":{"state":"MAGIC"}}')
  with self.assertRaises(EnrollmentError):CourierQueue(self.path)
 def test_concurrent_same_enqueue_converges(self):
  ctx=multiprocessing.get_context("fork");q=ctx.Queue()
  ps=[ctx.Process(target=_enqueue,args=(str(self.path),q)) for _ in range(8)]
  [x.start() for x in ps];[x.join() for x in ps];results=[q.get() for _ in ps]
  self.assertTrue(all(x[0]=="ok" for x in results))
  self.assertEqual(1,len({x[1] for x in results}))
  self.assertEqual(1,len(self.q.pending("rel")))
 def test_cancel_only_before_prepare(self):
  i=self.add();self.q.transition(i,expected="QUEUED",new="CANCELLED")
  self.assertEqual("CANCELLED",self.q.get(i)["state"])
 def test_wrong_expected_state_fails(self):
  i=self.add()
  with self.assertRaisesRegex(EnrollmentError,"state changed"):self.q.transition(i,expected="PREPARED",new="IN_FLIGHT",sequence=1)
