import tempfile,unittest
from pathlib import Path
from sentinel_forge.authenticity import TestOnlyHMACSigner,TestOnlyHMACVerifier
from sentinel_forge.enrollment import EnrollmentError,EnrollmentRegistry,build_bundle,install_bundle
from sentinel_forge.enrollment_lifecycle import GuardedEnrollmentLifecycle
from sentinel_forge.enrollment_proof import issue_challenge,authenticate_proof
from sentinel_forge.enrollment_session import ChallengeRegistry
from sentinel_forge.revocation import RevocationRegistry

class GuardedLifecycleTests(unittest.TestCase):
 def setUp(self):
  self.td=tempfile.TemporaryDirectory();r=Path(self.td.name);(r/"remote").mkdir()
  self.b=build_bundle(forge_identity="sentinel-forge",remote_identity="sentinel-reaper",remote_role="reaper",
   permitted_actions=["courier-receive"],permitted_target="sentinel-reaper",policy_reference="p1")
  self.p=install_bundle(self.b,expected_remote_identity="sentinel-reaper",root=r/"remote")
  self.life=GuardedEnrollmentLifecycle(EnrollmentRegistry(r/"e.json"),ChallengeRegistry(r/"c.json"),RevocationRegistry(r/"r.json"))
  self.s=TestOnlyHMACSigner("sentinel-reaper","rk",b"secret");self.v=TestOnlyHMACVerifier({("sentinel-reaper","rk"):b"secret"})
 def tearDown(self):self.td.cleanup()
 def stage_revoke(self):
  self.life.stage(self.b);self.life.revoke(self.b,operator_authorization_reference="op-1",reason="retire")
 def test_revoked_state_overrides_prior_state(self):
  self.stage_revoke();self.assertEqual("REVOKED",self.life.state(self.b.enrollment_id))
 def test_revoked_cannot_issue_challenge(self):
  self.stage_revoke();c=issue_challenge(self.b,nonce=b"0123456789abcdef")
  with self.assertRaises(EnrollmentError):self.life.issue_challenge(self.b,c)
 def test_revoked_cannot_accept_proof(self):
  self.stage_revoke()
  with self.assertRaises(EnrollmentError):self.life.accept_installation_proof(self.b,self.p)
 def test_revoked_cannot_activate(self):
  self.stage_revoke()
  with self.assertRaises(EnrollmentError):self.life.activate(self.b.enrollment_id,operator_approved=True)
 def test_revoked_cannot_be_staged_again(self):
  self.stage_revoke()
  with self.assertRaises(EnrollmentError):self.life.stage(self.b)
 def test_old_authenticated_proof_dies_after_revocation(self):
  self.life.stage(self.b);c=issue_challenge(self.b,nonce=b"0123456789abcdef");self.life.issue_challenge(self.b,c)
  a=authenticate_proof(self.b,c,self.p,self.s)
  self.life.revoke(self.b,operator_authorization_reference="op-2",reason="compromise")
  with self.assertRaises(EnrollmentError):self.life.verify_authenticated_remote(self.b,a,self.v,expected_remote_key_reference="rk")
 def test_unknown_enrollment_cannot_be_revoked(self):
  with self.assertRaises(EnrollmentError):self.life.revoke(self.b,operator_authorization_reference="op",reason="x")

if __name__=="__main__":unittest.main()

class AuthoritySurfaceTests(unittest.TestCase):
 def test_raw_enrollment_registry_has_no_activation_authority(self):
  self.assertFalse(hasattr(EnrollmentRegistry,"activate"))
 def test_guarded_lifecycle_is_activation_surface(self):
  self.assertTrue(hasattr(GuardedEnrollmentLifecycle,"activate"))

class ActivationCapabilityTests(unittest.TestCase):
 def test_raw_internal_transition_rejects_arbitrary_capability(self):
  with tempfile.TemporaryDirectory() as td:
   r=EnrollmentRegistry(Path(td)/"e.json")
   b=build_bundle(forge_identity="f",remote_identity="r",remote_role="r",
    permitted_actions=["receive"],permitted_target="r",policy_reference="p")
   r.stage(b)
   with self.assertRaises(EnrollmentError):
    r._transition_verified_to_active(b.enrollment_id,capability=object(),expected_capability=object())

class AuthenticatedRemotePrerequisiteTests(unittest.TestCase):
 def setUp(self):
  self.td=tempfile.TemporaryDirectory();r=Path(self.td.name);(r/"remote").mkdir()
  self.b=build_bundle(forge_identity="forge",remote_identity="reaper",remote_role="reaper",
   permitted_actions=["receive"],permitted_target="reaper",policy_reference="p")
  self.p=install_bundle(self.b,expected_remote_identity="reaper",root=r/"remote")
  self.er=EnrollmentRegistry(r/"e");self.life=GuardedEnrollmentLifecycle(self.er,ChallengeRegistry(r/"c"),RevocationRegistry(r/"r"))
  self.s=TestOnlyHMACSigner("reaper","rk",b"secret");self.v=TestOnlyHMACVerifier({("reaper","rk"):b"secret"})
 def tearDown(self):self.td.cleanup()
 def test_base_installation_proof_cannot_verify_staged_enrollment(self):
  self.life.stage(self.b)
  with self.assertRaisesRegex(EnrollmentError,"authenticated remote"):self.life.accept_installation_proof(self.b,self.p)
  self.assertEqual("STAGED",self.life.state(self.b.enrollment_id))
 def test_authenticated_challenge_advances_only_to_remote_authenticated(self):
  self.life.stage(self.b);c=issue_challenge(self.b,nonce=b"0123456789abcdef");self.life.issue_challenge(self.b,c)
  a=authenticate_proof(self.b,c,self.p,self.s);self.life.verify_authenticated_remote(self.b,a,self.v,expected_remote_key_reference="rk")
  self.assertEqual("REMOTE_AUTHENTICATED",self.life.state(self.b.enrollment_id))
 def test_installation_proof_after_authentication_advances_to_verified(self):
  self.life.stage(self.b);c=issue_challenge(self.b,nonce=b"0123456789abcdef");self.life.issue_challenge(self.b,c)
  a=authenticate_proof(self.b,c,self.p,self.s);self.life.verify_authenticated_remote(self.b,a,self.v,expected_remote_key_reference="rk")
  self.life.accept_installation_proof(self.b,self.p);self.assertEqual("VERIFIED",self.life.state(self.b.enrollment_id))
 def test_raw_remote_auth_transition_requires_internal_capability(self):
  self.er.stage(self.b)
  with self.assertRaises(EnrollmentError):
   self.er._mark_remote_authenticated(self.b.enrollment_id,capability=object(),expected_capability=object())
