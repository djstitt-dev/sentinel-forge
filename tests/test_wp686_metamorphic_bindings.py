import dataclasses,tempfile,unittest
from pathlib import Path
from sentinel_forge.credential_reference import build_credential_reference
from sentinel_forge.credential_registry import CredentialReferenceRegistry
from sentinel_forge.credential_session import bind_session_credential
from sentinel_forge.enrollment import EnrollmentError,build_bundle
from sentinel_forge.session import derive_session
from sentinel_forge.transport_contract import build_transport_context,validate_transport_context
from sentinel_forge.trust_domain import derive_trust_domain

class MetamorphicBindingTests(unittest.TestCase):
 def setUp(self):
  self.td=tempfile.TemporaryDirectory();r=Path(self.td.name);self.d=derive_trust_domain(build_bundle(forge_identity="forge",remote_identity="reaper",remote_role="reaper",permitted_actions=["receive"],permitted_target="reaper",policy_reference="p"));self.cr=CredentialReferenceRegistry(r/"c");self.c=build_credential_reference(self.d,generation=1,key_reference="k1");self.cr.register_initial(self.d,self.c);self.s=derive_session(self.d,generation=1,challenge=b"R"*32);self.b=bind_session_credential(self.s,self.d,self.c);self.h,self.x=build_transport_context(self.d,self.s,self.b,self.c,self.cr,operation="deliver",artifact_identity="a",sequence=1)
 def tearDown(self):self.td.cleanup()
 def verify(self,h=None,x=None):validate_transport_context(h or self.h,x or self.x,self.d,self.s,self.b,self.c,self.cr,expected_operation="deliver",expected_artifact_identity="a",expected_sequence=1)
 def test_original_valid(self):self.verify()
 def test_each_context_string_binding_mutation_rejected(self):
  fields=("relationship_id","session_id","key_reference","credential_binding_digest","protected_header_digest","context_digest")
  for f in fields:
   with self.subTest(field=f):
    x=dataclasses.replace(self.x,**{f:getattr(self.x,f)+"x"})
    with self.assertRaises(EnrollmentError):self.verify(x=x)
 def test_each_context_generation_mutation_rejected(self):
  for f in ("session_generation","credential_generation"):
   with self.subTest(field=f):
    x=dataclasses.replace(self.x,**{f:getattr(self.x,f)+1})
    with self.assertRaises(EnrollmentError):self.verify(x=x)
 def test_header_operation_mutation_rejected(self):
  with self.assertRaises(EnrollmentError):self.verify(h=dataclasses.replace(self.h,operation="other"))
 def test_header_artifact_mutation_rejected(self):
  with self.assertRaises(EnrollmentError):self.verify(h=dataclasses.replace(self.h,artifact_identity="evil"))
 def test_header_sequence_mutation_rejected(self):
  with self.assertRaises(EnrollmentError):self.verify(h=dataclasses.replace(self.h,sequence=2))
 def test_header_session_mutation_rejected(self):
  with self.assertRaises(EnrollmentError):self.verify(h=dataclasses.replace(self.h,session_id=self.h.session_id+"x"))
