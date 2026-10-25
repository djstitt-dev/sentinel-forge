import dataclasses, unittest
from sentinel_forge.authenticity import (AuthenticityError,TestOnlyHMACSigner,
 TestOnlyHMACVerifier,create_envelope,verify_envelope)

class AuthenticityTests(unittest.TestCase):
    def setUp(self):
        self.key=b"test-only-secret-not-for-artifacts"
        self.signer=TestOnlyHMACSigner("sentinel-forge","test-key-1",self.key)
        self.verifier=TestOnlyHMACVerifier({("sentinel-forge","test-key-1"):self.key})
        self.subject=b"canonical enrollment manifest\n"
    def test_valid_envelope_verifies(self):
        e=create_envelope(self.subject,self.signer)
        self.assertTrue(verify_envelope(self.subject,e,self.verifier,
          expected_signer_identity="sentinel-forge",expected_key_reference="test-key-1"))
    def test_modified_subject_fails(self):
        e=create_envelope(self.subject,self.signer)
        self.assertFalse(verify_envelope(self.subject+b"x",e,self.verifier,
          expected_signer_identity="sentinel-forge",expected_key_reference="test-key-1"))
    def test_wrong_expected_signer_fails(self):
        e=create_envelope(self.subject,self.signer)
        self.assertFalse(verify_envelope(self.subject,e,self.verifier,
          expected_signer_identity="other",expected_key_reference="test-key-1"))
    def test_wrong_key_reference_fails(self):
        e=create_envelope(self.subject,self.signer)
        self.assertFalse(verify_envelope(self.subject,e,self.verifier,
          expected_signer_identity="sentinel-forge",expected_key_reference="wrong"))
    def test_signature_tamper_fails(self):
        e=create_envelope(self.subject,self.signer)
        e=dataclasses.replace(e,signature="00"*32)
        self.assertFalse(verify_envelope(self.subject,e,self.verifier,
          expected_signer_identity="sentinel-forge",expected_key_reference="test-key-1"))
    def test_unknown_algorithm_fails(self):
        e=dataclasses.replace(create_envelope(self.subject,self.signer),algorithm="UNKNOWN")
        self.assertFalse(verify_envelope(self.subject,e,self.verifier,
          expected_signer_identity="sentinel-forge",expected_key_reference="test-key-1"))
    def test_empty_subject_rejected(self):
        with self.assertRaises(AuthenticityError): create_envelope(b"",self.signer)
    def test_test_signer_is_explicitly_nonproduction(self):
        self.assertTrue(self.signer.algorithm.startswith("TEST-ONLY-"))

if __name__=="__main__": unittest.main()

class ArtifactAuthenticityBoundaryTests(unittest.TestCase):
    def test_envelope_contains_reference_not_secret(self):
        key=b"do-not-export-this-secret"
        e=create_envelope(b"manifest",TestOnlyHMACSigner("forge","keyref",key))
        serialized=str(e.as_dict()).encode()
        self.assertNotIn(key,serialized)
        self.assertEqual("keyref",e.key_reference)
