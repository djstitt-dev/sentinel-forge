import unittest
from dataclasses import replace
from sentinel_forge.enrollment import EnrollmentError,build_bundle
from sentinel_forge.trust_domain import derive_trust_domain
from sentinel_forge.session import derive_session
from sentinel_forge.protected_message import (
 build_header,validate_header,associated_data,associated_data_digest,require_transport_ready_header,
)

def domain(peer,role):
 b=build_bundle(forge_identity="sentinel-forge",remote_identity=peer,remote_role=role,
  permitted_actions=["receive"],permitted_target=peer,policy_reference="policy:v1")
 return derive_trust_domain(b)

class ProtectedMessageContractTests(unittest.TestCase):
 def setUp(self):
  self.r=domain("sentinel-reaper","reaper");self.s=domain("sentinel-scribe","scribe")
  self.rs=derive_session(self.r,generation=1,challenge=b"R"*32)
  self.ss=derive_session(self.s,generation=1,challenge=b"S"*32)
  self.h=build_header(self.r,self.rs,operation="deliver",artifact_identity="sha256:artifact",sequence=7)
 def valid(self,h=None,domain_=None,session=None,**kw):
  validate_header(h or self.h,domain_ or self.r,session or self.rs,
   expected_operation=kw.get("operation","deliver"),
   expected_artifact_identity=kw.get("artifact","sha256:artifact"),
   expected_sequence=kw.get("sequence",7))
 def test_exact_relationship_and_session_header_validates(self):self.valid()
 def test_reaper_header_rejected_by_scribe_domain(self):
  with self.assertRaises(EnrollmentError):self.valid(domain_=self.s,session=self.ss)
 def test_peer_substitution_rejected(self):
  with self.assertRaises(EnrollmentError):self.valid(replace(self.h,peer_identity="sentinel-scribe"))
 def test_role_substitution_rejected(self):
  with self.assertRaises(EnrollmentError):self.valid(replace(self.h,peer_role="scribe"))
 def test_enrollment_substitution_rejected(self):
  with self.assertRaises(EnrollmentError):self.valid(replace(self.h,enrollment_id="enroll:evil"))
 def test_session_substitution_rejected(self):
  with self.assertRaises(EnrollmentError):self.valid(replace(self.h,session_id="session:evil"))
 def test_session_generation_substitution_rejected(self):
  with self.assertRaises(EnrollmentError):self.valid(replace(self.h,session_generation=2))
 def test_cross_relationship_session_rejected_at_construction(self):
  with self.assertRaises(EnrollmentError):
   build_header(self.r,self.ss,operation="deliver",artifact_identity="sha256:artifact",sequence=7)
 def test_operation_substitution_rejected(self):
  with self.assertRaises(EnrollmentError):self.valid(operation="activate")
 def test_artifact_substitution_rejected(self):
  with self.assertRaises(EnrollmentError):self.valid(artifact="sha256:other")
 def test_replay_sequence_mismatch_rejected(self):
  with self.assertRaises(EnrollmentError):self.valid(sequence=8)
 def test_zero_sequence_rejected(self):
  with self.assertRaises(EnrollmentError):
   build_header(self.r,self.rs,operation="deliver",artifact_identity="sha256:artifact",sequence=0)
 def test_associated_data_is_deterministic(self):
  other=build_header(self.r,self.rs,operation="deliver",artifact_identity="sha256:artifact",sequence=7)
  self.assertEqual(associated_data(self.h),associated_data(other))
 def test_cross_domain_associated_data_differs(self):
  sh=build_header(self.s,self.ss,operation="deliver",artifact_identity="sha256:artifact",sequence=7)
  self.assertNotEqual(associated_data_digest(self.h),associated_data_digest(sh))
 def test_transport_gate_accepts_bound_session(self):
  require_transport_ready_header(self.h,self.r,self.rs,expected_operation="deliver",
   expected_artifact_identity="sha256:artifact",expected_sequence=7)
 def test_transport_gate_rejects_forged_unbound_header(self):
  unbound=replace(self.h,session_id="SESSION_UNBOUND",session_generation=0)
  with self.assertRaises(EnrollmentError):
   require_transport_ready_header(unbound,self.r,self.rs,expected_operation="deliver",
    expected_artifact_identity="sha256:artifact",expected_sequence=7)
 def test_contract_contains_no_ciphertext_or_secret(self):
  d=self.h.as_dict()
  for k in ("ciphertext","key","secret","nonce","algorithm"):self.assertNotIn(k,d)

if __name__=="__main__":unittest.main()
