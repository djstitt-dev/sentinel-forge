import multiprocessing,tempfile,unittest
from pathlib import Path
from sentinel_forge.enrollment import EnrollmentError
from sentinel_forge.recovery_intent import RecoveryIntentLedger

def _prepare(path,q):
 try:q.put(("ok",RecoveryIntentLedger(Path(path)).prepare(plan_digest="p",target="t",observation_digest="o")))
 except Exception as exc:q.put(("err",type(exc).__name__))

class RecoveryIntentLedgerTests(unittest.TestCase):
 def setUp(self):
  self.td=tempfile.TemporaryDirectory();self.path=Path(self.td.name)/"recovery.json"
  self.r=RecoveryIntentLedger(self.path)
 def tearDown(self):self.td.cleanup()

 def test_prepare_apply_commit(self):
  iid=self.r.prepare(plan_digest="p",target="t",observation_digest="o")
  self.assertEqual("PREPARED",self.r.unresolved("p")["status"])
  self.r.mark_applied("p",iid);self.assertEqual("APPLIED",self.r.unresolved("p")["status"])
  self.r.commit("p",iid);self.assertIsNone(self.r.unresolved("p"))
  self.assertEqual("COMMITTED",self.r.record("p")["status"])

 def test_only_prepared_can_abort(self):
  iid=self.r.prepare(plan_digest="p",target="t",observation_digest="o");self.r.abort("p",iid)
  self.assertEqual("ABORTED",self.r.record("p")["status"])

 def test_applied_cannot_abort(self):
  iid=self.r.prepare(plan_digest="p",target="t",observation_digest="o");self.r.mark_applied("p",iid)
  with self.assertRaises(EnrollmentError):self.r.abort("p",iid)

 def test_unresolved_blocks_duplicate_prepare(self):
  self.r.prepare(plan_digest="p",target="t",observation_digest="o")
  with self.assertRaisesRegex(EnrollmentError,"RECOVERY_RECONCILIATION_REQUIRED"):
   self.r.prepare(plan_digest="p",target="t",observation_digest="o")

 def test_malformed_state_fails_closed(self):
  self.path.write_text('{"p":{"status":"MAGIC"}}')
  with self.assertRaisesRegex(EnrollmentError,"malformed recovery intent record"):RecoveryIntentLedger(self.path)

 def test_concurrent_prepare_has_one_winner(self):
  ctx=multiprocessing.get_context("fork");q=ctx.Queue()
  ps=[ctx.Process(target=_prepare,args=(str(self.path),q)) for _ in range(8)]
  [p.start() for p in ps];[p.join() for p in ps]
  results=[q.get() for _ in ps]
  self.assertEqual(1,sum(1 for x in results if x[0]=="ok"))
  self.assertEqual(7,sum(1 for x in results if x[0]=="err"))
