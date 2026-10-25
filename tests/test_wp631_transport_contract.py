import dataclasses,tempfile,unittest
from pathlib import Path
from sentinel_forge.credential_reference import build_credential_reference
from sentinel_forge.credential_registry import CredentialReferenceRegistry
from sentinel_forge.credential_session import bind_session_credential
from sentinel_forge.enrollment import EnrollmentError,build_bundle
from sentinel_forge.session import derive_session
from sentinel_forge.transport_contract import build_transport_context,validate_transport_context,associated_data
from sentinel_forge.trust_domain import derive_trust_domain

def domain(peer,role):
 return derive_trust_domain(build_bundle(forge_identity="sentinel-forge",remote_identity=peer,remote_role=role,
  permitted_actions=["receive"],permitted_target=peer,policy_reference="policy:v1"))

class TransportContractTests(unittest.TestCase):
 def setUp(self):
  self.td=tempfile.TemporaryDirectory();self.r=domain("sentinel-reaper","reaper")
  self.reg=CredentialReferenceRegistry(Path(self.td.name)/"c.json")
  self.c1=build_credential_reference(self.r,generation=1,key_reference="credential:reaper:g1")
  self.reg.register_initial(self.r,self.c1)
  self.s1=derive_session(self.r,generation=1,challenge=b"R"*32)
  self.b1=bind_session_credential(self.s1,self.r,self.c1)
  self.h,self.ctx=build_transport_context(self.r,self.s1,self.b1,self.c1,self.reg,
   operation="deliver",artifact_identity="sha256:artifact",sequence=1)
 def tearDown(self):self.td.cleanup()
 def valid(self):
  validate_transport_context(self.h,self.ctx,self.r,self.s1,self.b1,self.c1,self.reg,
   expected_operation="deliver",expected_artifact_identity="sha256:artifact",expected_sequence=1)
 def test_current_credential_message_context_validates(self):self.valid()
 def test_context_commits_to_credential_generation_and_reference(self):
  self.assertEqual(1,self.ctx.credential_generation);self.assertEqual("credential:reaper:g1",self.ctx.key_reference)
  self.assertEqual(self.b1.binding_digest,self.ctx.credential_binding_digest)
 def test_key_reference_substitution_rejected(self):
  with self.assertRaises(EnrollmentError):
   validate_transport_context(self.h,dataclasses.replace(self.ctx,key_reference="credential:evil"),self.r,self.s1,self.b1,self.c1,self.reg,
    expected_operation="deliver",expected_artifact_identity="sha256:artifact",expected_sequence=1)
 def test_credential_generation_substitution_rejected(self):
  with self.assertRaises(EnrollmentError):
   validate_transport_context(self.h,dataclasses.replace(self.ctx,credential_generation=2),self.r,self.s1,self.b1,self.c1,self.reg,
    expected_operation="deliver",expected_artifact_identity="sha256:artifact",expected_sequence=1)
 def test_rotation_kills_old_message_context(self):
  c2=build_credential_reference(self.r,generation=2,key_reference="credential:reaper:g2");self.reg.rotate(self.r,c2)
  with self.assertRaisesRegex(EnrollmentError,"stale"):self.valid()
 def test_new_generation_changes_associated_data(self):
  c2=build_credential_reference(self.r,generation=2,key_reference="credential:reaper:g2");self.reg.rotate(self.r,c2)
  s2=derive_session(self.r,generation=2,challenge=b"N"*32);b2=bind_session_credential(s2,self.r,c2)
  _,ctx2=build_transport_context(self.r,s2,b2,c2,self.reg,operation="deliver",artifact_identity="sha256:artifact",sequence=1)
  self.assertNotEqual(associated_data(self.ctx),associated_data(ctx2))
 def test_cross_peer_credential_cannot_construct_context(self):
  s=domain("sentinel-scribe","scribe")
  cs=build_credential_reference(s,generation=1,key_reference="credential:scribe:g1")
  with self.assertRaises(EnrollmentError):
   build_transport_context(self.r,self.s1,self.b1,cs,self.reg,operation="deliver",artifact_identity="sha256:artifact",sequence=1)
 def test_context_contains_no_secret_or_crypto_algorithm(self):
  d=self.ctx.as_dict()
  for k in ("secret","private_key","key_material","cipher","algorithm","nonce","ciphertext"):self.assertNotIn(k,d)

if __name__=="__main__":unittest.main()

class TransportAcceptanceGateTests(unittest.TestCase):
 def setUp(self):
  from sentinel_forge.session import ReplayRegistry
  self.td=tempfile.TemporaryDirectory();root=Path(self.td.name)
  self.d=domain("sentinel-reaper","reaper");self.reg=CredentialReferenceRegistry(root/"c.json")
  self.replay=ReplayRegistry(root/"replay.json")
  self.c=build_credential_reference(self.d,generation=1,key_reference="credential:reaper:g1");self.reg.register_initial(self.d,self.c)
  self.s=derive_session(self.d,generation=1,challenge=b"R"*32);self.b=bind_session_credential(self.s,self.d,self.c)
 def tearDown(self):self.td.cleanup()
 def message(self,seq):
  return build_transport_context(self.d,self.s,self.b,self.c,self.reg,operation="deliver",artifact_identity=f"sha256:a{seq}",sequence=seq)
 def accept(self,h,c,seq):
  from sentinel_forge.transport_contract import accept_transport_message
  accept_transport_message(h,c,self.d,self.s,self.b,self.c,self.reg,self.replay,
   expected_operation="deliver",expected_artifact_identity=f"sha256:a{seq}",expected_sequence=seq)
 def test_exact_next_message_is_accepted(self):
  h,c=self.message(1);self.accept(h,c,1);self.assertEqual(1,self.replay.state(self.d.relationship_id)["highest"])
 def test_replay_is_rejected(self):
  h,c=self.message(1);self.accept(h,c,1)
  with self.assertRaisesRegex(EnrollmentError,"replayed"):self.accept(h,c,1)
 def test_gap_is_rejected(self):
  h,c=self.message(1);self.accept(h,c,1);h2,c2=self.message(3)
  with self.assertRaisesRegex(EnrollmentError,"out-of-order"):self.accept(h2,c2,3)
 def test_invalid_context_does_not_consume_sequence(self):
  h,c=self.message(1);bad=dataclasses.replace(c,key_reference="credential:evil")
  with self.assertRaises(EnrollmentError):self.accept(h,bad,1)
  self.assertIsNone(self.replay.state(self.d.relationship_id))
  self.accept(h,c,1)
 def test_stale_credential_does_not_consume_next_sequence(self):
  h,c=self.message(1);h_old,c_old=self.message(2);self.accept(h,c,1)
  c2=build_credential_reference(self.d,generation=2,key_reference="credential:reaper:g2");self.reg.rotate(self.d,c2)
  with self.assertRaisesRegex(EnrollmentError,"stale"):self.accept(h_old,c_old,2)
  self.assertEqual(1,self.replay.state(self.d.relationship_id)["highest"])
