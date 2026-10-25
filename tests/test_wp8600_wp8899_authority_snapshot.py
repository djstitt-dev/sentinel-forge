import dataclasses,tempfile,unittest
from pathlib import Path
from sentinel_forge.authority_snapshot import *
from sentinel_forge.credential_reference import build_credential_reference
from sentinel_forge.credential_registry import CredentialReferenceRegistry
from sentinel_forge.credential_session import bind_session_credential
from sentinel_forge.enrollment import EnrollmentError,build_bundle
from sentinel_forge.send_sequence import SendSequenceRegistry
from sentinel_forge.session import derive_session,ReplayRegistry
from sentinel_forge.trust_domain import derive_trust_domain
class Snapshot(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();r=Path(self.t.name);self.send=SendSequenceRegistry(r/"s");self.recv=ReplayRegistry(r/"r");self.cr=CredentialReferenceRegistry(r/"c");self.d=derive_trust_domain(build_bundle(forge_identity="forge",remote_identity="reaper",remote_role="reaper",permitted_actions=["receive"],permitted_target="reaper",policy_reference="p"));self.c=build_credential_reference(self.d,generation=1,key_reference="k1");self.cr.register_initial(self.d,self.c);self.s=derive_session(self.d,generation=1,challenge=b"x"*16);self.b=bind_session_credential(self.s,self.d,self.c)
 def tearDown(self):self.t.cleanup()
 def args(self):return dict(domain=self.d,session=self.s,binding=self.b,credential=self.c,credential_registry=self.cr,send_registry=self.send,replay_registry=self.recv)
 def test_empty_sequence_authorities_snapshot(self):x=build_authority_snapshot(**self.args());self.assertEqual(0,x.send_highest);self.assertEqual(0,x.receive_highest);self.assertTrue(verify_authority_snapshot(x))
 def test_active_authorities_snapshot(self):
  self.send.reserve(self.s,self.d);self.recv.accept(self.s,self.d,sequence=1);x=build_authority_snapshot(**self.args());self.assertEqual((1,1),(x.send_highest,x.receive_highest))
 def test_snapshot_field_mutation_matrix(self):
  x=build_authority_snapshot(**self.args())
  for f in x.__dataclass_fields__:
   if f=="snapshot_digest":bad="sha256:bad"
   else:
    v=getattr(x,f);bad=(v+1 if isinstance(v,int) else ("x" if v is None else v+"x"))
   with self.subTest(f=f):
    with self.assertRaises(EnrollmentError):verify_authority_snapshot(dataclasses.replace(x,**{f:bad}))
 def test_stale_credential_rejected(self):
  c2=build_credential_reference(self.d,generation=2,key_reference="k2");self.cr.rotate(self.d,c2)
  with self.assertRaises(EnrollmentError):build_authority_snapshot(**self.args())
 def test_send_session_disagreement_rejected(self):
  self.send.reserve(self.s,self.d);c2=build_credential_reference(self.d,generation=2,key_reference="k2");self.cr.rotate(self.d,c2);s2=derive_session(self.d,generation=2,challenge=b"y"*16);b2=bind_session_credential(s2,self.d,c2)
  with self.assertRaises(EnrollmentError):build_authority_snapshot(**{**self.args(),"session":s2,"binding":b2,"credential":c2})
 def test_receive_session_disagreement_rejected(self):
  self.recv.accept(self.s,self.d,sequence=1);c2=build_credential_reference(self.d,generation=2,key_reference="k2");self.cr.rotate(self.d,c2);s2=derive_session(self.d,generation=2,challenge=b"y"*16);b2=bind_session_credential(s2,self.d,c2)
  with self.assertRaises(EnrollmentError):build_authority_snapshot(**{**self.args(),"session":s2,"binding":b2,"credential":c2})
