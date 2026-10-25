import unittest
from dataclasses import replace
from sentinel_forge.enrollment import EnrollmentError,build_bundle
from sentinel_forge.trust_domain import derive_trust_domain,verify_trust_domain,require_relationship,bind_message_context

def bundle(peer,role=None):
 return build_bundle(forge_identity="sentinel-forge",remote_identity=peer,remote_role=role or peer,
  permitted_actions=["receive"],permitted_target=peer,policy_reference="policy:v1")

class PairwiseTrustDomainTests(unittest.TestCase):
 def setUp(self):
  self.reaper=bundle("sentinel-reaper","reaper");self.scribe=bundle("sentinel-scribe","scribe")
  self.watch=bundle("sentinel-watchtower","watchtower")
  self.rd=derive_trust_domain(self.reaper);self.sd=derive_trust_domain(self.scribe);self.wd=derive_trust_domain(self.watch)
 def test_each_peer_has_distinct_relationship(self):
  self.assertEqual(3,len({self.rd.relationship_id,self.sd.relationship_id,self.wd.relationship_id}))
  self.assertEqual(3,len({self.rd.context_digest,self.sd.context_digest,self.wd.context_digest}))
 def test_reaper_domain_does_not_verify_as_scribe(self):
  self.assertFalse(verify_trust_domain(self.rd,self.scribe))
 def test_reaper_domain_does_not_verify_as_watchtower(self):
  self.assertFalse(verify_trust_domain(self.rd,self.watch))
 def test_wrong_peer_identity_fails_closed(self):
  with self.assertRaises(EnrollmentError):
   require_relationship(self.rd,forge_identity="sentinel-forge",peer_identity="sentinel-scribe",
    peer_role="reaper",enrollment_id=self.reaper.enrollment_id,permitted_target="sentinel-reaper")
 def test_wrong_role_fails_closed(self):
  with self.assertRaises(EnrollmentError):
   require_relationship(self.rd,forge_identity="sentinel-forge",peer_identity="sentinel-reaper",
    peer_role="scribe",enrollment_id=self.reaper.enrollment_id,permitted_target="sentinel-reaper")
 def test_wrong_enrollment_fails_closed(self):
  with self.assertRaises(EnrollmentError):
   require_relationship(self.rd,forge_identity="sentinel-forge",peer_identity="sentinel-reaper",
    peer_role="reaper",enrollment_id=self.scribe.enrollment_id,permitted_target="sentinel-reaper")
 def test_wrong_forge_identity_fails_closed(self):
  with self.assertRaises(EnrollmentError):
   require_relationship(self.rd,forge_identity="rogue-forge",peer_identity="sentinel-reaper",
    peer_role="reaper",enrollment_id=self.reaper.enrollment_id,permitted_target="sentinel-reaper")
 def test_tampered_domain_does_not_verify(self):
  self.assertFalse(verify_trust_domain(replace(self.rd,peer_identity="sentinel-scribe"),self.reaper))
 def test_message_context_is_relationship_specific(self):
  r=bind_message_context(self.rd,operation="deliver",artifact_identity="sha256:abc",sequence=1)
  s=bind_message_context(self.sd,operation="deliver",artifact_identity="sha256:abc",sequence=1)
  self.assertNotEqual(r,s)
 def test_message_context_binds_operation_artifact_and_sequence(self):
  base=bind_message_context(self.rd,operation="deliver",artifact_identity="sha256:abc",sequence=1)
  self.assertNotEqual(base,bind_message_context(self.rd,operation="verify",artifact_identity="sha256:abc",sequence=1))
  self.assertNotEqual(base,bind_message_context(self.rd,operation="deliver",artifact_identity="sha256:def",sequence=1))
  self.assertNotEqual(base,bind_message_context(self.rd,operation="deliver",artifact_identity="sha256:abc",sequence=2))
 def test_no_shared_fleet_secret_or_crypto_mechanism(self):
  d=self.rd.as_dict();self.assertNotIn("key",d);self.assertNotIn("secret",d);self.assertNotIn("cipher",d)
if __name__=="__main__":unittest.main()
