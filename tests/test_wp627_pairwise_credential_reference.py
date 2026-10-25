import dataclasses,unittest
from sentinel_forge.credential_reference import (
 build_credential_reference,require_rotation,validate_pairwise_credential_set,verify_credential_reference)
from sentinel_forge.enrollment import EnrollmentError,build_bundle
from sentinel_forge.trust_domain import derive_trust_domain

def domain(peer,role):
 b=build_bundle(forge_identity="sentinel-forge",remote_identity=peer,remote_role=role,
  permitted_actions=["receive"],permitted_target=peer,policy_reference="policy:v1")
 return derive_trust_domain(b)

class PairwiseCredentialReferenceTests(unittest.TestCase):
 def setUp(self):
  self.reaper=domain("sentinel-reaper","reaper")
  self.scribe=domain("sentinel-scribe","scribe")
  self.watch=domain("sentinel-watchtower","watchtower")
 def ref(self,d,g=1,k=None):
  return build_credential_reference(d,generation=g,key_reference=k or f"credential:{d.peer_identity}:g{g}")
 def test_reference_is_relationship_bound(self):
  r=self.ref(self.reaper)
  self.assertTrue(verify_credential_reference(r,self.reaper))
  self.assertFalse(verify_credential_reference(r,self.scribe))
 def test_three_peers_require_three_distinct_key_references(self):
  refs=[self.ref(self.reaper),self.ref(self.scribe),self.ref(self.watch)]
  validate_pairwise_credential_set(refs,[self.reaper,self.scribe,self.watch])
  self.assertEqual(3,len({r.key_reference for r in refs}))
 def test_fleet_wide_shared_key_reference_is_rejected(self):
  refs=[self.ref(self.reaper,k="credential:fleet:g1"),
        self.ref(self.scribe,k="credential:fleet:g1"),
        self.ref(self.watch,k="credential:fleet:g1")]
  with self.assertRaisesRegex(EnrollmentError,"fleet-wide credential reuse"):
   validate_pairwise_credential_set(refs,[self.reaper,self.scribe,self.watch])
 def test_missing_relationship_reference_is_rejected(self):
  with self.assertRaises(EnrollmentError):
   validate_pairwise_credential_set([self.ref(self.reaper)],[self.reaper,self.scribe])
 def test_duplicate_relationship_reference_is_rejected(self):
  r=self.ref(self.reaper)
  with self.assertRaises(EnrollmentError):
   validate_pairwise_credential_set([r,r],[self.reaper,self.scribe])
 def test_tampered_reference_fails(self):
  r=self.ref(self.reaper)
  self.assertFalse(verify_credential_reference(dataclasses.replace(r,peer_identity="sentinel-scribe"),self.reaper))
 def test_rotation_requires_exact_next_generation(self):
  old=self.ref(self.reaper,1);new=self.ref(self.reaper,2)
  require_rotation(old,new,self.reaper)
  with self.assertRaises(EnrollmentError):require_rotation(old,self.ref(self.reaper,3),self.reaper)
 def test_rotation_requires_new_key_reference(self):
  old=self.ref(self.reaper,1,k="credential:r")
  new=self.ref(self.reaper,2,k="credential:r")
  with self.assertRaisesRegex(EnrollmentError,"new key reference"):require_rotation(old,new,self.reaper)
 def test_rotation_cannot_cross_relationships(self):
  with self.assertRaises(EnrollmentError):
   require_rotation(self.ref(self.reaper,1),self.ref(self.scribe,2),self.reaper)
 def test_reference_contains_no_secret_or_crypto_selection(self):
  r=self.ref(self.reaper);d=r.as_dict()
  for forbidden in ("secret","private_key","cipher","algorithm","key_material"):
   self.assertNotIn(forbidden,d)

if __name__=="__main__":unittest.main()
