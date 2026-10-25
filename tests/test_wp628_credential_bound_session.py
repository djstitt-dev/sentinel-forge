import dataclasses,unittest
from sentinel_forge.credential_reference import build_credential_reference
from sentinel_forge.credential_session import (bind_session_credential,require_credential_ready_session,
 require_current_credential_session,verify_session_credential)
from sentinel_forge.enrollment import EnrollmentError,build_bundle
from sentinel_forge.session import derive_session
from sentinel_forge.trust_domain import derive_trust_domain

def domain(peer,role):
 return derive_trust_domain(build_bundle(forge_identity="sentinel-forge",remote_identity=peer,remote_role=role,
  permitted_actions=["receive"],permitted_target=peer,policy_reference="policy:v1"))

class CredentialBoundSessionTests(unittest.TestCase):
 def setUp(self):
  self.r=domain("sentinel-reaper","reaper");self.s=domain("sentinel-scribe","scribe")
  self.rc1=build_credential_reference(self.r,generation=1,key_reference="credential:reaper:g1")
  self.rs1=derive_session(self.r,generation=1,challenge=b"R"*32)
 def test_current_binding(self):
  b=bind_session_credential(self.rs1,self.r,self.rc1)
  self.assertTrue(verify_session_credential(b,self.rs1,self.r,self.rc1))
  require_current_credential_session(b,self.rs1,self.r,self.rc1)
 def test_cross_peer_reference_rejected(self):
  sc=build_credential_reference(self.s,generation=1,key_reference="credential:scribe:g1")
  with self.assertRaises(EnrollmentError):bind_session_credential(self.rs1,self.r,sc)
 def test_generation_mismatch_rejected(self):
  rc2=build_credential_reference(self.r,generation=2,key_reference="credential:reaper:g2")
  with self.assertRaisesRegex(EnrollmentError,"generation"):bind_session_credential(self.rs1,self.r,rc2)
 def test_rotation_invalidates_old_binding(self):
  old=bind_session_credential(self.rs1,self.r,self.rc1)
  rc2=build_credential_reference(self.r,generation=2,key_reference="credential:reaper:g2")
  rs2=derive_session(self.r,generation=2,challenge=b"2"*32)
  self.assertFalse(verify_session_credential(old,rs2,self.r,rc2))
  self.assertNotEqual(old.binding_digest,bind_session_credential(rs2,self.r,rc2).binding_digest)
 def test_old_reference_cannot_bind_new_generation(self):
  rs2=derive_session(self.r,generation=2,challenge=b"2"*32)
  with self.assertRaises(EnrollmentError):bind_session_credential(rs2,self.r,self.rc1)
 def test_tampered_reference_binding_rejected(self):
  b=bind_session_credential(self.rs1,self.r,self.rc1)
  self.assertFalse(verify_session_credential(dataclasses.replace(b,key_reference="credential:scribe:g1"),self.rs1,self.r,self.rc1))
 def test_binding_has_only_reference_metadata(self):
  d=bind_session_credential(self.rs1,self.r,self.rc1).as_dict()
  self.assertEqual("credential:reaper:g1",d["key_reference"])
  self.assertEqual(self.r.relationship_id,d["relationship_id"])
 def test_transport_gate_accepts_current_pairwise_binding(self):
  b=bind_session_credential(self.rs1,self.r,self.rc1)
  require_credential_ready_session(b,self.rs1,self.r,self.rc1)
 def test_transport_gate_rejects_stale_binding_after_rotation(self):
  old=bind_session_credential(self.rs1,self.r,self.rc1)
  rc2=build_credential_reference(self.r,generation=2,key_reference="credential:reaper:g2")
  rs2=derive_session(self.r,generation=2,challenge=b"2"*32)
  with self.assertRaises(EnrollmentError):
   require_credential_ready_session(old,rs2,self.r,rc2)

if __name__=="__main__":unittest.main()
