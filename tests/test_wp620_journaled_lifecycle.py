import json,tempfile,unittest
from pathlib import Path
from sentinel_forge.enrollment import EnrollmentError,EnrollmentRegistry,build_bundle,install_bundle
from sentinel_forge.authenticity import TestOnlyHMACSigner,TestOnlyHMACVerifier
from sentinel_forge.enrollment_proof import issue_challenge,authenticate_proof
from sentinel_forge.enrollment_lifecycle import GuardedEnrollmentLifecycle
from sentinel_forge.enrollment_session import ChallengeRegistry
from sentinel_forge.enrollment_state import EnrollmentStateJournal
from sentinel_forge.journaled_lifecycle import JournaledEnrollmentLifecycle
from sentinel_forge.revocation import RevocationRegistry

class JournaledLifecycleTests(unittest.TestCase):
 def setUp(self):
  self.td=tempfile.TemporaryDirectory();r=Path(self.td.name);(r/"remote").mkdir()
  self.b=build_bundle(forge_identity="forge",remote_identity="reaper",remote_role="reaper",
   permitted_actions=["receive"],permitted_target="reaper",policy_reference="p")
  self.p=install_bundle(self.b,expected_remote_identity="reaper",root=r/"remote")
  self.er=EnrollmentRegistry(r/"e.json")
  low=GuardedEnrollmentLifecycle(self.er,ChallengeRegistry(r/"c.json"),RevocationRegistry(r/"r.json"))
  self.j=EnrollmentStateJournal(r/"journal.jsonl");self.life=JournaledEnrollmentLifecycle(low,self.j)
  self.signer=TestOnlyHMACSigner("reaper","rk",b"secret");self.verifier=TestOnlyHMACVerifier({("reaper","rk"):b"secret"})
 def tearDown(self):self.td.cleanup()
 def stage_verify(self):
  self.life.stage(self.b,authorization_reference="op-stage")
  c=issue_challenge(self.b,nonce=b"0123456789abcdef");self.life.lifecycle.issue_challenge(self.b,c)
  a=authenticate_proof(self.b,c,self.p,self.signer)
  self.life.verify_authenticated_remote(self.b,a,self.verifier,expected_remote_key_reference="rk",authorization_reference="op-auth")
  self.life.accept_installation_proof(self.b,self.p,authorization_reference="op-proof")
 def test_full_journaled_lifecycle(self):
  self.stage_verify();self.life.activate(self.b,operator_approved=True,authorization_reference="op-active")
  self.assertEqual("ACTIVE",self.life.state(self.b.enrollment_id))
  self.life.revoke(self.b,operator_authorization_reference="op-revoke",reason="retire")
  self.assertEqual("REVOKED",self.life.state(self.b.enrollment_id))
 def test_registry_forged_active_disagrees_with_journal(self):
  self.life.stage(self.b,authorization_reference="op")
  db=json.loads(self.er.path.read_text());db[self.b.enrollment_id]["state"]="ACTIVE";self.er.path.write_text(json.dumps(db))
  with self.assertRaises(EnrollmentError):self.life.state(self.b.enrollment_id)
 def test_journal_blocks_activation_even_if_registry_says_verified(self):
  self.life.stage(self.b,authorization_reference="op")
  db=json.loads(self.er.path.read_text());db[self.b.enrollment_id]["state"]="VERIFIED";self.er.path.write_text(json.dumps(db))
  with self.assertRaises(EnrollmentError):self.life.activate(self.b,operator_approved=True,authorization_reference="op")
 def test_operator_denial_does_not_advance_journal(self):
  self.stage_verify()
  with self.assertRaises(EnrollmentError):self.life.activate(self.b,operator_approved=False,authorization_reference="op")
  self.assertEqual("VERIFIED",self.j.state(self.b.enrollment_id))
 def test_revoked_remains_terminal_in_journal(self):
  self.life.stage(self.b,authorization_reference="op")
  self.life.revoke(self.b,operator_authorization_reference="op-r",reason="retire")
  with self.assertRaises(EnrollmentError):self.life.stage(self.b,authorization_reference="again")

if __name__=="__main__":unittest.main()
