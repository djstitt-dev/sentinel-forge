import dataclasses,hashlib,tempfile,unittest
from pathlib import Path
from sentinel_forge.courier_receive import accept_inbound
from sentinel_forge.credential_reference import build_credential_reference
from sentinel_forge.credential_registry import CredentialReferenceRegistry
from sentinel_forge.credential_session import bind_session_credential
from sentinel_forge.enrollment import EnrollmentError,build_bundle
from sentinel_forge.session import ReplayRegistry,derive_session
from sentinel_forge.transport_contract import build_transport_context
from sentinel_forge.trust_domain import derive_trust_domain

class ReceiveTests(unittest.TestCase):
 def setUp(self):
  self.td=tempfile.TemporaryDirectory();root=Path(self.td.name);self.payload=b"artifact"
  self.aid="sha256:"+hashlib.sha256(self.payload).hexdigest()
  b=build_bundle(forge_identity="forge",remote_identity="reaper",remote_role="reaper",permitted_actions=["receive"],permitted_target="reaper",policy_reference="p")
  self.d=derive_trust_domain(b);self.cr=CredentialReferenceRegistry(root/"c.json");self.rr=ReplayRegistry(root/"r.json")
  self.c=build_credential_reference(self.d,generation=1,key_reference="cred:r:1");self.cr.register_initial(self.d,self.c)
  self.s=derive_session(self.d,generation=1,challenge=b"R"*32);self.cb=bind_session_credential(self.s,self.d,self.c)
  self.h,self.ctx=build_transport_context(self.d,self.s,self.cb,self.c,self.cr,operation="deliver",artifact_identity=self.aid,sequence=1)
 def tearDown(self):self.td.cleanup()
 def accept(self,payload=None,h=None,ctx=None):
  return accept_inbound(payload=self.payload if payload is None else payload,header=self.h if h is None else h,
   context=self.ctx if ctx is None else ctx,domain=self.d,session=self.s,binding=self.cb,credential=self.c,
   credential_registry=self.cr,replay_registry=self.rr,expected_operation="deliver",expected_artifact_identity=self.aid,expected_sequence=1)
 def test_valid_message_accepts_and_acks(self):
  r=self.accept();self.assertEqual("ACCEPTED",r.acknowledgement.disposition);self.assertEqual(1,self.rr.state(self.d.relationship_id)["highest"])
 def test_bad_payload_does_not_consume_sequence(self):
  with self.assertRaisesRegex(EnrollmentError,"artifact identity"):self.accept(payload=b"evil")
  self.assertIsNone(self.rr.state(self.d.relationship_id))
 def test_bad_context_does_not_consume_sequence(self):
  with self.assertRaises(EnrollmentError):self.accept(ctx=dataclasses.replace(self.ctx,key_reference="evil"))
  self.assertIsNone(self.rr.state(self.d.relationship_id))
 def test_replay_rejected(self):
  self.accept()
  with self.assertRaisesRegex(EnrollmentError,"replayed"):self.accept()
 def test_rotation_rejects_stale_without_consuming(self):
  c2=build_credential_reference(self.d,generation=2,key_reference="cred:r:2");self.cr.rotate(self.d,c2)
  with self.assertRaisesRegex(EnrollmentError,"stale"):self.accept()
  self.assertIsNone(self.rr.state(self.d.relationship_id))
