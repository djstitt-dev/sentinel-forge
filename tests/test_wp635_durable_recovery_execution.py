import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from sentinel_forge.enrollment import EnrollmentError
from sentinel_forge.evidence import EvidenceJournal
from sentinel_forge.recovery import build_plan,execute_durable_audited_safe_repair,observe
from sentinel_forge.recovery_intent import RecoveryIntentLedger

class DurableRecoveryExecutionTests(unittest.TestCase):
 def setUp(self):
  self.td=tempfile.TemporaryDirectory();r=Path(self.td.name)
  self.e=EvidenceJournal(r/"e.jsonl");self.i=RecoveryIntentLedger(r/"i.json")
  self.o=observe(condition="missing_local_index",target="index:a",observed_identity="id:a",details="absent")
  self.p=build_plan(self.o)
 def tearDown(self):self.td.cleanup()
 def run_repair(self,fn=lambda p:None):
  return execute_durable_audited_safe_repair(self.p,self.o,fn,self.e,self.i,actor="forge")

 def test_success_commits_and_records_evidence(self):
  self.assertEqual("REPAIRED",self.run_repair())
  self.assertEqual("COMMITTED",self.i.record(self.p.plan_digest)["status"])
  self.assertEqual(["REPAIR_ATTEMPT_REQUESTED","REPAIR_COMPLETED"],[x.outcome for x in self.e.verify()])

 def test_pre_audit_failure_aborts_without_repair(self):
  called=[]
  with patch.object(self.e,"append",side_effect=RuntimeError("audit")):
   with self.assertRaises(RuntimeError):self.run_repair(lambda p:called.append(p))
  self.assertEqual([],called);self.assertEqual("ABORTED",self.i.record(self.p.plan_digest)["status"])

 def test_repair_failure_aborts(self):
  with self.assertRaisesRegex(RuntimeError,"repair"):
   self.run_repair(lambda p:(_ for _ in ()).throw(RuntimeError("repair")))
  self.assertEqual("ABORTED",self.i.record(self.p.plan_digest)["status"])

 def test_completion_audit_failure_leaves_applied(self):
  original=self.e.append;count={"n":0}
  def second_fails(**kw):
   count["n"]+=1
   if count["n"]==2:raise RuntimeError("audit")
   return original(**kw)
  with patch.object(self.e,"append",side_effect=second_fails):
   with self.assertRaisesRegex(EnrollmentError,"repair applied"):
    self.run_repair()
  self.assertEqual("APPLIED",self.i.unresolved(self.p.plan_digest)["status"])

 def test_applied_blocks_blind_retry(self):
  iid=self.i.prepare(plan_digest=self.p.plan_digest,target=self.p.target,observation_digest=self.p.observation_digest)
  self.i.mark_applied(self.p.plan_digest,iid);called=[]
  with self.assertRaisesRegex(EnrollmentError,"RECOVERY_RECONCILIATION_REQUIRED"):
   self.run_repair(lambda p:called.append(p))
  self.assertEqual([],called)

 def test_non_safe_plan_never_prepares_intent(self):
  o=observe(condition="revoked_relationship",target="peer:a",observed_identity="revoked",details="terminal")
  p=build_plan(o)
  with self.assertRaisesRegex(EnrollmentError,"TERMINAL"):
   execute_durable_audited_safe_repair(p,o,lambda x:None,self.e,self.i,actor="forge")
  self.assertIsNone(self.i.record(p.plan_digest))
