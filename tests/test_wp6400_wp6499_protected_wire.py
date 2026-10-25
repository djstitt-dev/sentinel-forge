import dataclasses,tempfile,unittest
from pathlib import Path
from sentinel_forge.credential_reference import build_credential_reference
from sentinel_forge.credential_registry import CredentialReferenceRegistry
from sentinel_forge.credential_session import bind_session_credential
from sentinel_forge.enrollment import EnrollmentError,build_bundle
from sentinel_forge.protected_wire import encode,decode
from sentinel_forge.session import derive_session
from sentinel_forge.transport_contract import build_transport_context
from sentinel_forge.trust_domain import derive_trust_domain
class P:
 provider_id="TEST-P"
 def protect(self,p,*,associated_data,key_reference):
  k=(sum(associated_data)+sum(key_reference.encode()))%251+1;return bytes(x^k for x in p)
 def unprotect(self,p,*,associated_data,key_reference):return self.protect(p,associated_data=associated_data,key_reference=key_reference)
class WireTests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.root=Path(self.t.name);b=build_bundle(forge_identity="forge",remote_identity="reaper",remote_role="reaper",permitted_actions=["receive"],permitted_target="reaper",policy_reference="p");self.d=derive_trust_domain(b)
  self.r=CredentialReferenceRegistry(self.root/"c");self.c=build_credential_reference(self.d,generation=1,key_reference="k1");self.r.register_initial(self.d,self.c);self.s=derive_session(self.d,generation=1,challenge=b"x"*16);self.b=bind_session_credential(self.s,self.d,self.c)
  self.h,self.ctx=build_transport_context(self.d,self.s,self.b,self.c,self.r,operation="deliver",artifact_identity="sha256:a",sequence=1);self.p=P()
 def tearDown(self):self.t.cleanup()
 def args(self):return dict(header=self.h,context=self.ctx,domain=self.d,session=self.s,binding=self.b,credential=self.c,credential_registry=self.r,provider=self.p)
 def test_roundtrip(self):
  w=encode(plaintext=b"payload",**self.args());self.assertEqual(b"payload",decode(wire=w,**self.args()))
 def test_wire_does_not_contain_plaintext(self):
  w=encode(plaintext=b"super-secret-plaintext",**self.args());self.assertNotIn(b"super-secret-plaintext",w.frame_bytes)
 def test_frame_mutation_rejected_matrix(self):
  w=encode(plaintext=b"payload",**self.args())
  for i in range(min(len(w.frame_bytes),96)):
   with self.subTest(i=i):
    x=bytearray(w.frame_bytes);x[i]^=1
    with self.assertRaises(EnrollmentError):decode(wire=dataclasses.replace(w,frame_bytes=bytes(x)),**self.args())
 def test_provider_identity_substitution_rejected(self):
  w=encode(plaintext=b"payload",**self.args())
  with self.assertRaises(EnrollmentError):decode(wire=dataclasses.replace(w,provider_id="other"),**self.args())
 def test_key_reference_substitution_rejected(self):
  w=encode(plaintext=b"payload",**self.args())
  with self.assertRaises(EnrollmentError):decode(wire=dataclasses.replace(w,key_reference="other"),**self.args())
 def test_header_operation_substitution_rejected(self):
  w=encode(plaintext=b"payload",**self.args())
  with self.assertRaises(EnrollmentError):decode(wire=w,**{**self.args(),"header":dataclasses.replace(self.h,operation="other")})
 def test_header_artifact_substitution_rejected(self):
  w=encode(plaintext=b"payload",**self.args())
  with self.assertRaises(EnrollmentError):decode(wire=w,**{**self.args(),"header":dataclasses.replace(self.h,artifact_identity="other")})
 def test_header_sequence_substitution_rejected(self):
  w=encode(plaintext=b"payload",**self.args())
  with self.assertRaises(EnrollmentError):decode(wire=w,**{**self.args(),"header":dataclasses.replace(self.h,sequence=2)})
 def test_context_field_mutation_matrix(self):
  w=encode(plaintext=b"payload",**self.args())
  for f in self.ctx.__dataclass_fields__:
   old=getattr(self.ctx,f)
   if isinstance(old,int):bad=old+1
   else:bad=old+"x"
   with self.subTest(field=f):
    with self.assertRaises(EnrollmentError):decode(wire=w,**{**self.args(),"context":dataclasses.replace(self.ctx,**{f:bad})})
 def test_rotation_kills_old_wire(self):
  w=encode(plaintext=b"payload",**self.args());c2=build_credential_reference(self.d,generation=2,key_reference="k2");self.r.rotate(self.d,c2)
  with self.assertRaises(EnrollmentError):decode(wire=w,**self.args())
