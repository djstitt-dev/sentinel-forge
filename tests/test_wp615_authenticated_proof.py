import dataclasses,tempfile,unittest
from pathlib import Path
from sentinel_forge.authenticity import TestOnlyHMACSigner,TestOnlyHMACVerifier
from sentinel_forge.enrollment import EnrollmentError,build_bundle,install_bundle
from sentinel_forge.enrollment_proof import issue_challenge,authenticate_proof,verify_authenticated_proof

class AuthenticatedProofTests(unittest.TestCase):
    def setUp(self):
        self.td=tempfile.TemporaryDirectory(); root=Path(self.td.name); (root/"remote").mkdir()
        self.b=build_bundle(forge_identity="sentinel-forge",remote_identity="sentinel-reaper",
          remote_role="reaper",permitted_actions=["courier-receive"],permitted_target="sentinel-reaper",
          policy_reference="p1")
        self.p=install_bundle(self.b,expected_remote_identity="sentinel-reaper",root=root/"remote")
        self.s=TestOnlyHMACSigner("sentinel-reaper","remote-test-key",b"remote-test-secret")
        self.v=TestOnlyHMACVerifier({("sentinel-reaper","remote-test-key"):b"remote-test-secret"})
        self.c=issue_challenge(self.b,nonce=b"0123456789abcdef")
    def tearDown(self):self.td.cleanup()
    def auth(self):return authenticate_proof(self.b,self.c,self.p,self.s)
    def verify(self,a,challenge=None):
        return verify_authenticated_proof(self.b,a,self.v,expected_remote_key_reference="remote-test-key",
          expected_challenge_id=challenge or self.c.challenge_id)
    def test_valid_remote_authenticated_proof(self):self.assertTrue(self.verify(self.auth()))
    def test_wrong_challenge_blocks_replay(self):self.assertFalse(self.verify(self.auth(),"challenge:other"))
    def test_modified_proof_fails(self):
        a=self.auth(); bad=dataclasses.replace(a,proof=dataclasses.replace(a.proof,remote_role="scribe"))
        self.assertFalse(self.verify(bad))
    def test_modified_challenge_fails(self):
        a=self.auth(); bad=dataclasses.replace(a,challenge=dataclasses.replace(a.challenge,remote_identity="other"))
        self.assertFalse(self.verify(bad))
    def test_wrong_remote_signer_rejected_at_creation(self):
        s=TestOnlyHMACSigner("other","remote-test-key",b"remote-test-secret")
        with self.assertRaises(EnrollmentError):authenticate_proof(self.b,self.c,self.p,s)
    def test_wrong_remote_key_reference_fails(self):
        a=self.auth()
        self.assertFalse(verify_authenticated_proof(self.b,a,self.v,expected_remote_key_reference="wrong",
          expected_challenge_id=self.c.challenge_id))
    def test_short_challenge_nonce_rejected(self):
        with self.assertRaises(EnrollmentError):issue_challenge(self.b,nonce=b"short")
    def test_challenge_bound_to_exact_enrollment(self):
        other=dataclasses.replace(self.b,remote_identity="sentinel-watchtower")
        with self.assertRaises(EnrollmentError):authenticate_proof(other,self.c,self.p,self.s)

if __name__=="__main__":unittest.main()
