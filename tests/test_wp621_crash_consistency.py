import multiprocessing,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from sentinel_forge.enrollment import EnrollmentError,EnrollmentRegistry,build_bundle,install_bundle
from sentinel_forge.enrollment_lifecycle import GuardedEnrollmentLifecycle
from sentinel_forge.authenticity import TestOnlyHMACSigner,TestOnlyHMACVerifier
from sentinel_forge.enrollment_proof import issue_challenge,authenticate_proof
from sentinel_forge.enrollment_session import ChallengeRegistry
from sentinel_forge.enrollment_state import EnrollmentStateJournal
from sentinel_forge.journaled_lifecycle import JournaledEnrollmentLifecycle
from sentinel_forge.revocation import RevocationRegistry
from sentinel_forge.transition_intent import TransitionIntentLedger



def _prepare_worker(path,enrollment_id,queue):
 try:
  iid=TransitionIntentLedger(Path(path)).prepare(
   enrollment_id=enrollment_id,remote_identity="reaper",from_state="STAGED",to_state="VERIFIED",
   authorization_reference="op",reason="concurrent test")
  queue.put(("PREPARED",iid))
 except Exception as exc:
  queue.put((type(exc).__name__,str(exc)))

class CrashConsistencyTests(unittest.TestCase):
 def setUp(self):
  self.td=tempfile.TemporaryDirectory();self.r=Path(self.td.name);(self.r/"remote").mkdir()
  self.b=build_bundle(forge_identity="forge",remote_identity="reaper",remote_role="reaper",
   permitted_actions=["receive"],permitted_target="reaper",policy_reference="p")
  self.p=install_bundle(self.b,expected_remote_identity="reaper",root=self.r/"remote")
  self.er=EnrollmentRegistry(self.r/"e.json")
  self.low=GuardedEnrollmentLifecycle(self.er,ChallengeRegistry(self.r/"c.json"),RevocationRegistry(self.r/"r.json"))
  self.j=EnrollmentStateJournal(self.r/"journal.jsonl");self.i=TransitionIntentLedger(self.r/"intent.json")
  self.life=JournaledEnrollmentLifecycle(self.low,self.j,self.i)
 def tearDown(self):self.td.cleanup()
 def restart(self):return JournaledEnrollmentLifecycle(self.low,EnrollmentStateJournal(self.r/"journal.jsonl"),TransitionIntentLedger(self.r/"intent.json"))
 def test_failure_during_mutation_leaves_prepared_and_blocks_restart(self):
  with patch.object(self.low,"stage",side_effect=RuntimeError("crash")):
   with self.assertRaises(RuntimeError):self.life.stage(self.b,authorization_reference="op")
  self.assertEqual("PREPARED",self.i.unresolved(self.b.enrollment_id)["status"])
  with self.assertRaisesRegex(EnrollmentError,"RECONCILIATION_REQUIRED"):self.restart().state(self.b.enrollment_id)
 def test_failure_after_mutation_before_journal_blocks_restart(self):
  original=self.j.transition
  with patch.object(self.j,"transition",side_effect=OSError("disk failure")):
   with self.assertRaises(OSError):self.life.stage(self.b,authorization_reference="op")
  self.assertEqual("MUTATED",self.i.unresolved(self.b.enrollment_id)["status"])
  self.assertEqual("STAGED",self.low.state(self.b.enrollment_id));self.assertIsNone(EnrollmentStateJournal(self.r/"journal.jsonl").state(self.b.enrollment_id))
  with self.assertRaisesRegex(EnrollmentError,"RECONCILIATION_REQUIRED"):self.restart().state(self.b.enrollment_id)
 def test_failure_after_journal_before_commit_blocks_restart(self):
  real_commit=self.i.commit
  with patch.object(self.i,"commit",side_effect=OSError("crash")):
   with self.assertRaises(OSError):self.life.stage(self.b,authorization_reference="op")
  self.assertEqual("MUTATED",self.i.unresolved(self.b.enrollment_id)["status"])
  self.assertEqual("STAGED",self.j.state(self.b.enrollment_id))
  with self.assertRaisesRegex(EnrollmentError,"RECONCILIATION_REQUIRED"):self.restart().state(self.b.enrollment_id)
 def test_success_commits_intent(self):
  self.life.stage(self.b,authorization_reference="op")
  self.assertIsNone(self.i.unresolved(self.b.enrollment_id));self.assertEqual("STAGED",self.life.state(self.b.enrollment_id))
 def test_unresolved_intent_blocks_blind_retry(self):
  with patch.object(self.j,"transition",side_effect=OSError("disk")):
   with self.assertRaises(OSError):self.life.stage(self.b,authorization_reference="op")
  with self.assertRaisesRegex(EnrollmentError,"RECONCILIATION_REQUIRED"):self.restart().stage(self.b,authorization_reference="op2")

if __name__=="__main__":unittest.main()

class IntentLedgerFailClosedTests(unittest.TestCase):
 def test_malformed_ledger_fails_closed(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"i.json";p.write_text("{broken")
   with self.assertRaises(EnrollmentError):TransitionIntentLedger(p)
 def test_non_mapping_ledger_fails_closed(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"i.json";p.write_text("[]")
   with self.assertRaises(EnrollmentError):TransitionIntentLedger(p)

class KnownRejectionIntentTests(unittest.TestCase):
 def test_operator_denial_aborts_intent_instead_of_forcing_reconciliation(self):
  with tempfile.TemporaryDirectory() as td:
   r=Path(td);(r/"remote").mkdir()
   from sentinel_forge.enrollment import install_bundle
   b=build_bundle(forge_identity="forge",remote_identity="reaper",remote_role="reaper",
    permitted_actions=["receive"],permitted_target="reaper",policy_reference="p")
   proof=install_bundle(b,expected_remote_identity="reaper",root=r/"remote")
   er=EnrollmentRegistry(r/"e.json");low=GuardedEnrollmentLifecycle(er,ChallengeRegistry(r/"c.json"),RevocationRegistry(r/"r.json"))
   j=EnrollmentStateJournal(r/"j");i=TransitionIntentLedger(r/"i");life=JournaledEnrollmentLifecycle(low,j,i)
   life.stage(b,authorization_reference="s")
   c=issue_challenge(b,nonce=b"0123456789abcdef");low.issue_challenge(b,c)
   signer=TestOnlyHMACSigner("reaper","rk",b"secret");verifier=TestOnlyHMACVerifier({("reaper","rk"):b"secret"})
   a=authenticate_proof(b,c,proof,signer)
   life.verify_authenticated_remote(b,a,verifier,expected_remote_key_reference="rk",authorization_reference="auth")
   life.accept_installation_proof(b,proof,authorization_reference="v")
   with self.assertRaises(EnrollmentError):life.activate(b,operator_approved=False,authorization_reference="deny")
   self.assertIsNone(i.unresolved(b.enrollment_id));self.assertEqual("VERIFIED",life.state(b.enrollment_id))


class IntentLedgerConcurrencyTests(unittest.TestCase):
 def test_multiprocess_prepare_has_exactly_one_winner(self):
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/"intent.json";eid="enrollment:test";q=multiprocessing.Queue()
   ps=[multiprocessing.Process(target=_prepare_worker,args=(str(path),eid,q)) for _ in range(8)]
   for proc in ps:proc.start()
   for proc in ps:proc.join(5)
   self.assertTrue(all(not proc.is_alive() and proc.exitcode==0 for proc in ps),
                   [(proc.pid,proc.exitcode) for proc in ps])
   results=[q.get(timeout=2) for _ in ps]
   self.assertEqual(1,sum(1 for x in results if x[0]=="PREPARED"),results)
   losers=[x for x in results if x[0]=="EnrollmentError"]
   self.assertEqual(7,len(losers),results)
   self.assertTrue(all("RECONCILIATION_REQUIRED" in x[1] for x in losers),results)
   record=TransitionIntentLedger(path).unresolved(eid)
   self.assertIsNotNone(record);self.assertEqual("PREPARED",record["status"])
