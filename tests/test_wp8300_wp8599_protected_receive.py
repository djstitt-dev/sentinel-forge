import dataclasses,hashlib,tempfile,unittest
from pathlib import Path
from sentinel_forge.credential_reference import build_credential_reference
from sentinel_forge.credential_registry import CredentialReferenceRegistry
from sentinel_forge.credential_session import bind_session_credential
from sentinel_forge.enrollment import EnrollmentError,build_bundle
from sentinel_forge.protected_receive import accept_protected_inbound
from sentinel_forge.protected_wire import encode
from sentinel_forge.session import derive_session,ReplayRegistry
from sentinel_forge.transport_contract import build_transport_context
from sentinel_forge.trust_domain import derive_trust_domain
class P:
 provider_id="TEST-P"
 def protect(self,p,*,associated_data,key_reference):
  k=(sum(associated_data)+sum(key_reference.encode()))%251+1;return bytes(x^k for x in p)
 def unprotect(self,p,*,associated_data,key_reference):return self.protect(p,associated_data=associated_data,key_reference=key_reference)
class Receive(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();r=Path(self.t.name);self.rr=ReplayRegistry(r/"replay");self.cr=CredentialReferenceRegistry(r/"cred");self.p=P()
  self.d=derive_trust_domain(build_bundle(forge_identity="forge",remote_identity="reaper",remote_role="reaper",permitted_actions=["receive"],permitted_target="reaper",policy_reference="p"))
  self.c=build_credential_reference(self.d,generation=1,key_reference="k1");self.cr.register_initial(self.d,self.c);self.s=derive_session(self.d,generation=1,challenge=b"x"*16);self.b=bind_session_credential(self.s,self.d,self.c)
  self.payload=b"payload";self.a="sha256:"+hashlib.sha256(self.payload).hexdigest();self.h,self.x=build_transport_context(self.d,self.s,self.b,self.c,self.cr,operation="deliver",artifact_identity=self.a,sequence=1);self.w=encode(plaintext=self.payload,header=self.h,context=self.x,domain=self.d,session=self.s,binding=self.b,credential=self.c,credential_registry=self.cr,provider=self.p)
 def tearDown(self):self.t.cleanup()
 def args(self):return dict(wire=self.w,header=self.h,context=self.x,domain=self.d,session=self.s,binding=self.b,credential=self.c,credential_registry=self.cr,replay_registry=self.rr,provider=self.p,expected_operation="deliver",expected_artifact_identity=self.a,expected_sequence=1)
 def test_valid_consumes_sequence_and_acks(self):
  r=accept_protected_inbound(**self.args());self.assertEqual(self.payload,r.plaintext);self.assertEqual(1,self.rr.state(self.d.relationship_id)["highest"])
 def test_replay_rejected(self):
  accept_protected_inbound(**self.args())
  with self.assertRaises(EnrollmentError):accept_protected_inbound(**self.args())
 def test_frame_mutation_matrix_never_consumes_replay(self):
  for i in range(min(100,len(self.w.frame_bytes))):
   with self.subTest(i=i):
    x=bytearray(self.w.frame_bytes);x[i]^=1;bad=dataclasses.replace(self.w,frame_bytes=bytes(x))
    with self.assertRaises(EnrollmentError):accept_protected_inbound(**{**self.args(),"wire":bad})
    self.assertIsNone(self.rr.state(self.d.relationship_id))
 def test_wrong_expected_artifact_never_consumes(self):
  with self.assertRaises(EnrollmentError):accept_protected_inbound(**{**self.args(),"expected_artifact_identity":"sha256:bad"})
  self.assertIsNone(self.rr.state(self.d.relationship_id))
 def test_wrong_operation_never_consumes(self):
  with self.assertRaises(EnrollmentError):accept_protected_inbound(**{**self.args(),"expected_operation":"other"})
  self.assertIsNone(self.rr.state(self.d.relationship_id))
 def test_wrong_sequence_never_consumes(self):
  with self.assertRaises(EnrollmentError):accept_protected_inbound(**{**self.args(),"expected_sequence":2})
  self.assertIsNone(self.rr.state(self.d.relationship_id))
 def test_wrong_provider_never_consumes(self):
  class Q(P):provider_id="Q"
  with self.assertRaises(EnrollmentError):accept_protected_inbound(**{**self.args(),"provider":Q()})
  self.assertIsNone(self.rr.state(self.d.relationship_id))
 def test_rotation_before_receive_never_consumes(self):
  c2=build_credential_reference(self.d,generation=2,key_reference="k2");self.cr.rotate(self.d,c2)
  with self.assertRaises(EnrollmentError):accept_protected_inbound(**self.args())
  self.assertIsNone(self.rr.state(self.d.relationship_id))
