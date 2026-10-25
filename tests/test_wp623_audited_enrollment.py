import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from sentinel_forge.audited_enrollment import AuditedEnrollmentLifecycle,AuditedEnrollmentReconciler,AuditOutcomeUnknown
from sentinel_forge.enrollment import EnrollmentRegistry,build_bundle,install_bundle
from sentinel_forge.enrollment_lifecycle import GuardedEnrollmentLifecycle
from sentinel_forge.authenticity import TestOnlyHMACSigner,TestOnlyHMACVerifier
from sentinel_forge.enrollment_proof import issue_challenge,authenticate_proof
from sentinel_forge.enrollment_session import ChallengeRegistry
from sentinel_forge.enrollment_state import EnrollmentStateJournal
from sentinel_forge.evidence import EvidenceJournal,EvidenceError
from sentinel_forge.journaled_lifecycle import JournaledEnrollmentLifecycle
from sentinel_forge.reconciliation import EnrollmentReconciler
from sentinel_forge.revocation import RevocationRegistry
from sentinel_forge.transition_intent import TransitionIntentLedger

class AuditedEnrollmentTests(unittest.TestCase):
 def setUp(self):
  self.td=tempfile.TemporaryDirectory();r=Path(self.td.name);(r/"remote").mkdir()
  self.b=build_bundle(forge_identity="forge",remote_identity="reaper",remote_role="reaper",
   permitted_actions=["receive"],permitted_target="reaper",policy_reference="p")
  self.proof=install_bundle(self.b,expected_remote_identity="reaper",root=r/"remote")
  er=EnrollmentRegistry(r/"e.json");low=GuardedEnrollmentLifecycle(er,ChallengeRegistry(r/"c.json"),RevocationRegistry(r/"r.json"))
  self.state=EnrollmentStateJournal(r/"s.jsonl");self.intents=TransitionIntentLedger(r/"i.json")
  core=JournaledEnrollmentLifecycle(low,self.state,self.intents);self.ev=EvidenceJournal(r/"evidence.jsonl")
  self.a=AuditedEnrollmentLifecycle(core,self.ev);self.core=core;self.low=low
 def tearDown(self):self.td.cleanup()
 def test_stage_emits_attempt_and_completion(self):
  self.a.stage(self.b,authorization_reference="op")
  self.assertEqual(["AUTHORITY_ATTEMPT_REQUESTED","AUTHORITY_ACTION_COMPLETED"],[x.outcome for x in self.ev.verify()])
 def test_pre_audit_failure_blocks_authority_change(self):
  with patch.object(self.ev,"append",side_effect=EvidenceError("disk")):
   with self.assertRaises(EvidenceError):self.a.stage(self.b,authorization_reference="op")
  self.assertIsNone(self.state.state(self.b.enrollment_id));self.assertIsNone(self.low.state(self.b.enrollment_id))
 def test_final_audit_failure_does_not_claim_operation_failed(self):
  calls=0;real=self.ev.append
  def append(**kw):
   nonlocal calls;calls+=1
   if calls==2:raise EvidenceError("disk")
   return real(**kw)
  with patch.object(self.ev,"append",side_effect=append):
   with self.assertRaises(AuditOutcomeUnknown):self.a.stage(self.b,authorization_reference="op")
  with self.assertRaisesRegex(Exception,"RECONCILIATION_REQUIRED"):
   self.core.state(self.b.enrollment_id)
  self.assertEqual("STAGED",self.state.state(self.b.enrollment_id))
  self.assertEqual("STAGED",self.low.state(self.b.enrollment_id))
  pending=self.intents.unresolved(self.b.enrollment_id)
  self.assertIsNotNone(pending);self.assertEqual("MUTATED",pending["status"])
  self.assertEqual(["AUTHORITY_ATTEMPT_REQUESTED"],[x.outcome for x in self.ev.verify()])
 def test_successful_stage_commits_only_after_completion_audit(self):
  seen=[]
  real=self.ev.append
  def append(**kw):
   event=real(**kw);seen.append((kw["outcome"],self.intents.unresolved(self.b.enrollment_id)));return event
  with patch.object(self.ev,"append",side_effect=append):
   self.a.stage(self.b,authorization_reference="op")
  self.assertEqual("AUTHORITY_ATTEMPT_REQUESTED",seen[0][0])
  self.assertIsNone(seen[0][1])
  self.assertEqual("AUTHORITY_ACTION_COMPLETED",seen[1][0])
  self.assertIsNotNone(seen[1][1]);self.assertEqual("MUTATED",seen[1][1]["status"])
  self.assertIsNone(self.intents.unresolved(self.b.enrollment_id))
  self.assertEqual("STAGED",self.core.state(self.b.enrollment_id))
 def test_activation_completion_audit_failure_leaves_active_reconciliation_required(self):
  self.a.stage(self.b,authorization_reference="s")
  c=issue_challenge(self.b,nonce=b"0123456789abcdef");self.low.issue_challenge(self.b,c)
  signer=TestOnlyHMACSigner("reaper","rk",b"secret");verifier=TestOnlyHMACVerifier({("reaper","rk"):b"secret"})
  authenticated=authenticate_proof(self.b,c,self.proof,signer)
  self.a.verify_authenticated_remote(self.b,authenticated,verifier,
   expected_remote_key_reference="rk",authorization_reference="auth")
  self.a.accept_installation_proof(self.b,self.proof,authorization_reference="v")
  calls=0;real=self.ev.append
  def append(**kw):
   nonlocal calls;calls+=1
   if calls==2:raise EvidenceError("disk")
   return real(**kw)
  with patch.object(self.ev,"append",side_effect=append):
   with self.assertRaises(AuditOutcomeUnknown):
    self.a.activate(self.b,operator_approved=True,authorization_reference="activate")
  self.assertEqual("ACTIVE",self.state.state(self.b.enrollment_id))
  self.assertEqual("ACTIVE",self.low.state(self.b.enrollment_id))
  pending=self.intents.unresolved(self.b.enrollment_id)
  self.assertIsNotNone(pending);self.assertEqual("MUTATED",pending["status"])
  with self.assertRaisesRegex(Exception,"RECONCILIATION_REQUIRED"):
   self.core.state(self.b.enrollment_id)
  rec=EnrollmentReconciler(journal=self.state,intents=self.intents,lifecycle=self.low)
  assessment=rec.assess(self.b.enrollment_id)
  self.assertEqual("COMPLETED",assessment.conclusion)
  self.assertEqual("ACTIVE",assessment.journal_state);self.assertEqual("ACTIVE",assessment.lifecycle_state)
 def test_activation_denial_is_failure_not_completion(self):
  self.a.stage(self.b,authorization_reference="s")
  c=issue_challenge(self.b,nonce=b"0123456789abcdef");self.low.issue_challenge(self.b,c)
  signer=TestOnlyHMACSigner("reaper","rk",b"secret");verifier=TestOnlyHMACVerifier({("reaper","rk"):b"secret"})
  a=authenticate_proof(self.b,c,self.proof,signer)
  self.core.verify_authenticated_remote(self.b,a,verifier,expected_remote_key_reference="rk",authorization_reference="auth")
  self.a.accept_installation_proof(self.b,self.proof,authorization_reference="v")
  with self.assertRaises(Exception):self.a.activate(self.b,operator_approved=False,authorization_reference="a")
  self.assertEqual("VERIFIED",self.core.state(self.b.enrollment_id))
  self.assertEqual("AUTHORITY_ACTION_FAILED",self.ev.verify()[-1].outcome)

class AuditedReconciliationTests(unittest.TestCase):
 def test_pre_audit_failure_blocks_reconciliation(self):
  with tempfile.TemporaryDirectory() as td:
   r=Path(td);j=EnrollmentStateJournal(r/"s");i=TransitionIntentLedger(r/"i")
   class L:
    def state(self,e):return None
   i.prepare(enrollment_id="e",remote_identity="r",from_state=None,to_state="STAGED",authorization_reference="a",reason="x")
   rec=EnrollmentReconciler(journal=j,intents=i,lifecycle=L());ev=EvidenceJournal(r/"ev")
   a=AuditedEnrollmentReconciler(rec,ev)
   with patch.object(ev,"append",side_effect=EvidenceError("disk")):
    with self.assertRaises(EvidenceError):a.resolve("e",operator_approved=True,authorization_reference="op",expected_conclusion="NOT_APPLIED")
   self.assertIsNotNone(i.unresolved("e"))

if __name__=="__main__":unittest.main()

class AuditedRemoteAuthenticationTests(unittest.TestCase):
 def test_remote_authentication_is_available_through_audited_surface(self):
  with tempfile.TemporaryDirectory() as td:
   r=Path(td);(r/"remote").mkdir()
   from sentinel_forge.authenticity import TestOnlyHMACSigner,TestOnlyHMACVerifier
   from sentinel_forge.enrollment_proof import issue_challenge,authenticate_proof
   b=build_bundle(forge_identity="forge",remote_identity="reaper",remote_role="reaper",
    permitted_actions=["receive"],permitted_target="reaper",policy_reference="p")
   proof=install_bundle(b,expected_remote_identity="reaper",root=r/"remote")
   low=GuardedEnrollmentLifecycle(EnrollmentRegistry(r/"e"),ChallengeRegistry(r/"c"),RevocationRegistry(r/"r"))
   core=JournaledEnrollmentLifecycle(low,EnrollmentStateJournal(r/"s"),TransitionIntentLedger(r/"i"))
   ev=EvidenceJournal(r/"ev");a=AuditedEnrollmentLifecycle(core,ev)
   a.stage(b,authorization_reference="stage")
   c=issue_challenge(b,nonce=b"0123456789abcdef");low.issue_challenge(b,c)
   signer=TestOnlyHMACSigner("reaper","rk",b"secret");verifier=TestOnlyHMACVerifier({("reaper","rk"):b"secret"})
   ap=authenticate_proof(b,c,proof,signer)
   self.assertTrue(a.verify_authenticated_remote(b,ap,verifier,expected_remote_key_reference="rk",authorization_reference="auth"))
   self.assertEqual("REMOTE_AUTHENTICATED",core.state(b.enrollment_id))
   self.assertEqual("AUTHORITY_ACTION_COMPLETED",ev.verify()[-1].outcome)
