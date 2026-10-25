import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from sentinel_forge.enrollment import EnrollmentError,EnrollmentRegistry,build_bundle
from sentinel_forge.enrollment_lifecycle import GuardedEnrollmentLifecycle
from sentinel_forge.authenticity import TestOnlyHMACSigner,TestOnlyHMACVerifier
from sentinel_forge.enrollment_proof import issue_challenge,authenticate_proof
from sentinel_forge.enrollment_session import ChallengeRegistry
from sentinel_forge.enrollment_state import EnrollmentStateJournal
from sentinel_forge.journaled_lifecycle import JournaledEnrollmentLifecycle
from sentinel_forge.reconciliation import EnrollmentReconciler
from sentinel_forge.revocation import RevocationRegistry
from sentinel_forge.transition_intent import TransitionIntentLedger

class ReconciliationTests(unittest.TestCase):
 def setUp(self):
  self.td=tempfile.TemporaryDirectory();r=Path(self.td.name)
  self.b=build_bundle(forge_identity="forge",remote_identity="reaper",remote_role="reaper",
   permitted_actions=["receive"],permitted_target="reaper",policy_reference="p")
  self.er=EnrollmentRegistry(r/"e.json")
  self.low=GuardedEnrollmentLifecycle(self.er,ChallengeRegistry(r/"c.json"),RevocationRegistry(r/"r.json"))
  self.j=EnrollmentStateJournal(r/"j.jsonl");self.i=TransitionIntentLedger(r/"i.json")
  self.life=JournaledEnrollmentLifecycle(self.low,self.j,self.i)
  self.rec=EnrollmentReconciler(journal=self.j,intents=self.i,lifecycle=self.low)
 def tearDown(self):self.td.cleanup()
 def crash_before_mutation(self):
  with patch.object(self.low,"stage",side_effect=RuntimeError("crash")):
   with self.assertRaises(RuntimeError):self.life.stage(self.b,authorization_reference="op")
 def crash_after_journal(self):
  with patch.object(self.i,"commit",side_effect=OSError("crash")):
   with self.assertRaises(OSError):self.life.stage(self.b,authorization_reference="op")
 def test_prepared_with_neither_store_changed_is_not_applied(self):
  self.crash_before_mutation();self.assertEqual("NOT_APPLIED",self.rec.assess(self.b.enrollment_id).conclusion)
 def test_completed_but_uncommitted_is_detected(self):
  self.crash_after_journal();self.assertEqual("COMPLETED",self.rec.assess(self.b.enrollment_id).conclusion)
 def test_completed_requires_operator_approval(self):
  self.crash_after_journal()
  with self.assertRaises(EnrollmentError):self.rec.resolve(self.b.enrollment_id,operator_approved=False,authorization_reference="op-r",expected_conclusion="COMPLETED")
 def test_completed_resolution_only_commits_existing_effect(self):
  self.crash_after_journal()
  self.assertEqual("COMMITTED",self.rec.resolve(self.b.enrollment_id,operator_approved=True,authorization_reference="op-r",expected_conclusion="COMPLETED"))
  self.assertEqual("STAGED",self.life.state(self.b.enrollment_id))
 def test_not_applied_may_be_aborted_with_operator_approval(self):
  self.crash_before_mutation()
  self.assertEqual("ABORTED",self.rec.resolve(self.b.enrollment_id,operator_approved=True,authorization_reference="op-r",expected_conclusion="NOT_APPLIED"))
  self.assertIsNone(self.life.state(self.b.enrollment_id))
 def test_ambiguous_cannot_be_resolved(self):
  self.crash_before_mutation()
  self.er.stage(self.b)
  a=self.rec.assess(self.b.enrollment_id);self.assertEqual("AMBIGUOUS",a.conclusion)
  with self.assertRaisesRegex(EnrollmentError,"ambiguous"):self.rec.resolve(self.b.enrollment_id,operator_approved=True,authorization_reference="op-r",expected_conclusion="AMBIGUOUS")
 def test_stale_assessment_cannot_be_used(self):
  self.crash_before_mutation();self.er.stage(self.b)
  with self.assertRaises(EnrollmentError):self.rec.resolve(self.b.enrollment_id,operator_approved=True,authorization_reference="op-r",expected_conclusion="NOT_APPLIED")
 def test_reconciler_never_writes_authority_state(self):
  self.crash_before_mutation()
  before=self.j.path.read_bytes()
  self.rec.resolve(self.b.enrollment_id,operator_approved=True,authorization_reference="op-r",expected_conclusion="NOT_APPLIED")
  self.assertEqual(before,self.j.path.read_bytes())

if __name__=="__main__":unittest.main()

class ActivationReconciliationTests(unittest.TestCase):
 def setUp(self):
  self.td=tempfile.TemporaryDirectory();r=Path(self.td.name);(r/"remote").mkdir()
  from sentinel_forge.enrollment import install_bundle
  self.b=build_bundle(forge_identity="forge",remote_identity="reaper",remote_role="reaper",
   permitted_actions=["receive"],permitted_target="reaper",policy_reference="p")
  proof=install_bundle(self.b,expected_remote_identity="reaper",root=r/"remote")
  self.er=EnrollmentRegistry(r/"e.json")
  self.low=GuardedEnrollmentLifecycle(self.er,ChallengeRegistry(r/"c.json"),RevocationRegistry(r/"r.json"))
  self.j=EnrollmentStateJournal(r/"j.jsonl");self.i=TransitionIntentLedger(r/"i.json")
  self.life=JournaledEnrollmentLifecycle(self.low,self.j,self.i)
  self.life.stage(self.b,authorization_reference="s")
  c=issue_challenge(self.b,nonce=b"0123456789abcdef");self.low.issue_challenge(self.b,c)
  signer=TestOnlyHMACSigner("reaper","rk",b"secret");verifier=TestOnlyHMACVerifier({("reaper","rk"):b"secret"})
  a=authenticate_proof(self.b,c,proof,signer)
  self.life.verify_authenticated_remote(self.b,a,verifier,expected_remote_key_reference="rk",authorization_reference="auth")
  self.life.accept_installation_proof(self.b,proof,authorization_reference="v")
  self.rec=EnrollmentReconciler(journal=self.j,intents=self.i,lifecycle=self.low)
 def tearDown(self):self.td.cleanup()
 def test_activation_crash_after_effect_is_ambiguous_not_active(self):
  with patch.object(self.j,"transition",side_effect=OSError("disk")):
   with self.assertRaises(OSError):self.life.activate(self.b,operator_approved=True,authorization_reference="a")
  a=self.rec.assess(self.b.enrollment_id)
  self.assertEqual("AMBIGUOUS",a.conclusion)
  self.assertEqual("VERIFIED",a.journal_state);self.assertEqual("ACTIVE",a.lifecycle_state)
  with self.assertRaises(EnrollmentError):self.life.state(self.b.enrollment_id)
  with self.assertRaisesRegex(EnrollmentError,"ambiguous"):self.rec.resolve(self.b.enrollment_id,operator_approved=True,authorization_reference="r",expected_conclusion="AMBIGUOUS")
 def test_activation_crash_after_both_stores_can_commit_only_existing_active(self):
  with patch.object(self.i,"commit",side_effect=OSError("crash")):
   with self.assertRaises(OSError):self.life.activate(self.b,operator_approved=True,authorization_reference="a")
  a=self.rec.assess(self.b.enrollment_id);self.assertEqual("COMPLETED",a.conclusion)
  self.rec.resolve(self.b.enrollment_id,operator_approved=True,authorization_reference="r",expected_conclusion="COMPLETED")
  self.assertEqual("ACTIVE",self.life.state(self.b.enrollment_id))
 def test_reconciliation_cannot_upgrade_verified_to_active(self):
  iid=self.i.prepare(enrollment_id=self.b.enrollment_id,remote_identity=self.b.remote_identity,
   from_state="VERIFIED",to_state="ACTIVE",authorization_reference="a",reason="operator activation")
  self.assertEqual("NOT_APPLIED",self.rec.assess(self.b.enrollment_id).conclusion)
  self.rec.resolve(self.b.enrollment_id,operator_approved=True,authorization_reference="r",expected_conclusion="NOT_APPLIED")
  self.assertEqual("VERIFIED",self.life.state(self.b.enrollment_id))

class RemoteAuthenticationCrashReconciliationTests(unittest.TestCase):
 def setUp(self):
  self.td=tempfile.TemporaryDirectory();r=Path(self.td.name);(r/"remote").mkdir()
  from sentinel_forge.enrollment import install_bundle
  self.b=build_bundle(forge_identity="forge",remote_identity="reaper",remote_role="reaper",
   permitted_actions=["receive"],permitted_target="reaper",policy_reference="p")
  self.proof=install_bundle(self.b,expected_remote_identity="reaper",root=r/"remote")
  self.er=EnrollmentRegistry(r/"e.json");self.ch=ChallengeRegistry(r/"c.json")
  self.low=GuardedEnrollmentLifecycle(self.er,self.ch,RevocationRegistry(r/"r.json"))
  self.j=EnrollmentStateJournal(r/"j.jsonl");self.i=TransitionIntentLedger(r/"i.json")
  self.life=JournaledEnrollmentLifecycle(self.low,self.j,self.i)
  self.life.stage(self.b,authorization_reference="stage")
  self.challenge=issue_challenge(self.b,nonce=b"0123456789abcdef")
  self.low.issue_challenge(self.b,self.challenge)
  signer=TestOnlyHMACSigner("reaper","rk",b"secret")
  self.verifier=TestOnlyHMACVerifier({("reaper","rk"):b"secret"})
  self.authenticated=authenticate_proof(self.b,self.challenge,self.proof,signer)
  self.rec=EnrollmentReconciler(journal=self.j,intents=self.i,lifecycle=self.low)
 def tearDown(self):self.td.cleanup()
 def verify(self):
  return self.life.verify_authenticated_remote(self.b,self.authenticated,self.verifier,
   expected_remote_key_reference="rk",authorization_reference="auth")
 def test_failure_before_challenge_verification_is_not_applied(self):
  with patch.object(self.low,"verify_authenticated_remote",side_effect=RuntimeError("crash-before-proof")):
   with self.assertRaises(RuntimeError):self.verify()
  a=self.rec.assess(self.b.enrollment_id)
  self.assertEqual("OUTSTANDING",a.challenge_state)
  self.assertEqual("NOT_APPLIED",a.conclusion)
 def test_consumed_challenge_without_authority_transition_is_ambiguous(self):
  original=self.er._mark_remote_authenticated
  def crash_after_consume(*args,**kwargs):raise RuntimeError("crash-after-consume")
  with patch.object(self.er,"_mark_remote_authenticated",side_effect=crash_after_consume):
   with self.assertRaises(RuntimeError):self.verify()
  a=self.rec.assess(self.b.enrollment_id)
  self.assertEqual("CONSUMED",a.challenge_state)
  self.assertEqual("STAGED",a.journal_state);self.assertEqual("STAGED",a.lifecycle_state)
  self.assertEqual("AMBIGUOUS",a.conclusion)
  with self.assertRaisesRegex(EnrollmentError,"ambiguous"):
   self.rec.resolve(self.b.enrollment_id,operator_approved=True,authorization_reference="recover",
    expected_conclusion="AMBIGUOUS")
  with self.assertRaisesRegex(EnrollmentError,"RECONCILIATION_REQUIRED"):self.life.state(self.b.enrollment_id)
 def test_registry_advanced_before_authority_journal_is_ambiguous(self):
  with patch.object(self.j,"transition",side_effect=OSError("journal-crash")):
   with self.assertRaises(OSError):self.verify()
  a=self.rec.assess(self.b.enrollment_id)
  self.assertEqual("CONSUMED",a.challenge_state)
  self.assertEqual("STAGED",a.journal_state);self.assertEqual("REMOTE_AUTHENTICATED",a.lifecycle_state)
  self.assertEqual("AMBIGUOUS",a.conclusion)
 def test_authority_journal_advanced_before_intent_commit_is_completed(self):
  with patch.object(self.i,"commit",side_effect=OSError("commit-crash")):
   with self.assertRaises(OSError):self.verify()
  a=self.rec.assess(self.b.enrollment_id)
  self.assertEqual("CONSUMED",a.challenge_state)
  self.assertEqual("REMOTE_AUTHENTICATED",a.journal_state)
  self.assertEqual("REMOTE_AUTHENTICATED",a.lifecycle_state)
  self.assertEqual("COMPLETED",a.conclusion)
  self.assertEqual("COMMITTED",self.rec.resolve(self.b.enrollment_id,operator_approved=True,
   authorization_reference="recover",expected_conclusion="COMPLETED"))
  self.assertEqual("REMOTE_AUTHENTICATED",self.life.state(self.b.enrollment_id))
