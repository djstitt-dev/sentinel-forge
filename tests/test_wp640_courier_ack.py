import dataclasses,tempfile,unittest
from pathlib import Path
from sentinel_forge.courier_ack import build_ack,verify_ack
from sentinel_forge.credential_reference import build_credential_reference
from sentinel_forge.credential_registry import CredentialReferenceRegistry
from sentinel_forge.credential_session import bind_session_credential
from sentinel_forge.enrollment import EnrollmentError,build_bundle
from sentinel_forge.session import derive_session
from sentinel_forge.transport_contract import build_transport_context
from sentinel_forge.trust_domain import derive_trust_domain

class CourierAckTests(unittest.TestCase):
 def setUp(self):
  self.td=tempfile.TemporaryDirectory();root=Path(self.td.name)
  b=build_bundle(forge_identity="forge",remote_identity="reaper",remote_role="reaper",permitted_actions=["receive"],permitted_target="reaper",policy_reference="p")
  self.d=derive_trust_domain(b);self.r=CredentialReferenceRegistry(root/"c.json")
  self.c=build_credential_reference(self.d,generation=1,key_reference="cred:r:1");self.r.register_initial(self.d,self.c)
  self.s=derive_session(self.d,generation=1,challenge=b"R"*32);cb=bind_session_credential(self.s,self.d,self.c)
  _,self.ctx=build_transport_context(self.d,self.s,cb,self.c,self.r,operation="deliver",artifact_identity="sha256:a",sequence=1)
  self.a=build_ack(self.ctx,sequence=1,operation="deliver",artifact_identity="sha256:a",disposition="ACCEPTED",reason="stored")
 def tearDown(self):self.td.cleanup()
 def test_exact_ack_validates(self):verify_ack(self.a,self.ctx,sequence=1,operation="deliver",artifact_identity="sha256:a")
 def test_sequence_substitution_rejected(self):
  with self.assertRaises(EnrollmentError):verify_ack(self.a,self.ctx,sequence=2,operation="deliver",artifact_identity="sha256:a")
 def test_artifact_substitution_rejected(self):
  with self.assertRaises(EnrollmentError):verify_ack(self.a,self.ctx,sequence=1,operation="deliver",artifact_identity="sha256:b")
 def test_context_substitution_rejected(self):
  bad=dataclasses.replace(self.ctx,context_digest="sha256:evil")
  with self.assertRaises(EnrollmentError):verify_ack(self.a,bad,sequence=1,operation="deliver",artifact_identity="sha256:a")
 def test_ack_tamper_rejected(self):
  with self.assertRaises(EnrollmentError):verify_ack(dataclasses.replace(self.a,reason="different"),self.ctx,sequence=1,operation="deliver",artifact_identity="sha256:a")
 def test_unknown_disposition_rejected(self):
  with self.assertRaises(EnrollmentError):build_ack(self.ctx,sequence=1,operation="deliver",artifact_identity="sha256:a",disposition="MAYBE",reason="x")
