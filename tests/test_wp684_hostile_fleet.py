import hashlib,tempfile,unittest
from pathlib import Path
from sentinel_forge.courier_ack import build_ack,verify_ack
from sentinel_forge.credential_reference import build_credential_reference
from sentinel_forge.credential_registry import CredentialReferenceRegistry
from sentinel_forge.credential_session import bind_session_credential
from sentinel_forge.enrollment import EnrollmentError,build_bundle
from sentinel_forge.session import ReplayRegistry,derive_session
from sentinel_forge.transport_contract import build_transport_context,validate_transport_context
from sentinel_forge.trust_domain import derive_trust_domain

class HostileFleetTests(unittest.TestCase):
 def setUp(self):self.td=tempfile.TemporaryDirectory();self.r=Path(self.td.name);self.cr=CredentialReferenceRegistry(self.r/"c")
 def tearDown(self):self.td.cleanup()
 def peer(self,name):
  d=derive_trust_domain(build_bundle(forge_identity="forge",remote_identity=name,remote_role=name,permitted_actions=["receive"],permitted_target=name,policy_reference="p"))
  c=build_credential_reference(d,generation=1,key_reference="key:"+name);self.cr.register_initial(d,c);s=derive_session(d,generation=1,challenge=(name.encode()*32)[:32]);b=bind_session_credential(s,d,c);return d,c,s,b
 def context(self,x,artifact="a",seq=1):d,c,s,b=x;return build_transport_context(d,s,b,c,self.cr,operation="deliver",artifact_identity=artifact,sequence=seq)
 def test_reaper_context_rejected_as_scribe(self):
  reaper=self.peer("reaper");scribe=self.peer("scribe");header,ctx=self.context(reaper)
  d,c,s,b=scribe
  with self.assertRaises(EnrollmentError):validate_transport_context(header,ctx,d,s,b,c,self.cr,expected_operation="deliver",expected_artifact_identity="a",expected_sequence=1)
 def test_ack_artifact_substitution_rejected(self):
  x=self.peer("reaper");header,ctx=self.context(x,artifact="a");ack=build_ack(ctx,sequence=1,operation="deliver",artifact_identity="b",disposition="ACCEPTED",reason="x")
  with self.assertRaises(EnrollmentError):verify_ack(ack,ctx,operation="deliver",artifact_identity="a",sequence=1)
 def test_old_session_context_dies_after_rotation(self):
  d,c,s,b=self.peer("reaper");header,ctx=self.context((d,c,s,b));c2=build_credential_reference(d,generation=2,key_reference="key:reaper:2");self.cr.rotate(d,c2);s2=derive_session(d,generation=2,challenge=b"N"*32);b2=bind_session_credential(s2,d,c2)
  with self.assertRaises(EnrollmentError):validate_transport_context(header,ctx,d,s2,b2,c2,self.cr,expected_operation="deliver",expected_artifact_identity="a",expected_sequence=1)
 def test_receive_gap_and_duplicate_fail(self):
  d,c,s,b=self.peer("watchtower");rr=ReplayRegistry(self.r/"replay")
  rr.accept(s,d,sequence=1)
  with self.assertRaises(EnrollmentError):rr.accept(s,d,sequence=1)
  with self.assertRaises(EnrollmentError):rr.accept(s,d,sequence=3)
  rr.accept(s,d,sequence=2);self.assertEqual(2,rr.state(d.relationship_id)["highest"])
