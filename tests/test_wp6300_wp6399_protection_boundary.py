import unittest
from sentinel_forge.enrollment import EnrollmentError
from sentinel_forge.protection_provider import protect,unprotect,ProtectedPayload
class XorTestProvider:
 provider_id="TEST-ONLY-XOR"
 def protect(self,p,*,associated_data,key_reference):
  k=(sum(associated_data)+sum(key_reference.encode()))%251+1;return bytes(x^k for x in p)
 def unprotect(self,p,*,associated_data,key_reference):return self.protect(p,associated_data=associated_data,key_reference=key_reference)
class Echo:
 provider_id="BAD-ECHO"
 def protect(self,p,**kw):return p
 def unprotect(self,p,**kw):return p
class Fail:
 provider_id="FAIL"
 def protect(self,*a,**k):raise RuntimeError("boom")
 def unprotect(self,*a,**k):raise RuntimeError("boom")
class Empty:
 provider_id="EMPTY"
 def protect(self,*a,**k):return b""
 def unprotect(self,*a,**k):return b""
class ProtectionBoundary(unittest.TestCase):
 def setUp(self):self.p=XorTestProvider();self.pt=b"secret-message";self.ad=b"exact-associated-data";self.k="key:ref:1"
 def test_roundtrip(self):
  x=protect(self.p,self.pt,associated_data=self.ad,key_reference=self.k);self.assertNotEqual(self.pt,x.protected_bytes);self.assertEqual(self.pt,unprotect(self.p,x,associated_data=self.ad,key_reference=self.k))
 def test_plaintext_fallback_rejected(self):
  with self.assertRaisesRegex(EnrollmentError,"plaintext fallback"):protect(Echo(),self.pt,associated_data=self.ad,key_reference=self.k)
 def test_provider_failure_matrix(self):
  with self.assertRaises(EnrollmentError):protect(Fail(),self.pt,associated_data=self.ad,key_reference=self.k)
  with self.assertRaises(EnrollmentError):unprotect(Fail(),ProtectedPayload("FAIL",self.k,b"x"),associated_data=self.ad,key_reference=self.k)
 def test_empty_provider_output_rejected(self):
  with self.assertRaises(EnrollmentError):protect(Empty(),self.pt,associated_data=self.ad,key_reference=self.k)
  with self.assertRaises(EnrollmentError):unprotect(Empty(),ProtectedPayload("EMPTY",self.k,b"x"),associated_data=self.ad,key_reference=self.k)
 def test_input_type_matrix(self):
  bad=(None,"x",bytearray(b"x"),1,True,[],{})
  for x in bad:
   with self.subTest(kind=type(x).__name__):
    with self.assertRaises(EnrollmentError):protect(self.p,x,associated_data=self.ad,key_reference=self.k)
 def test_associated_data_type_matrix(self):
  for x in (None,"x",bytearray(b"x"),b"",1,True):
   with self.subTest(kind=repr(x)):
    with self.assertRaises(EnrollmentError):protect(self.p,self.pt,associated_data=x,key_reference=self.k)
 def test_key_reference_matrix(self):
  for x in (None,"", " ",1,True,b"x"):
   with self.subTest(kind=repr(x)):
    with self.assertRaises(EnrollmentError):protect(self.p,self.pt,associated_data=self.ad,key_reference=x)
 def test_wrong_key_reference_rejected_before_provider(self):
  x=protect(self.p,self.pt,associated_data=self.ad,key_reference=self.k)
  with self.assertRaisesRegex(EnrollmentError,"binding"):unprotect(self.p,x,associated_data=self.ad,key_reference="other")
 def test_wrong_provider_rejected(self):
  x=protect(self.p,self.pt,associated_data=self.ad,key_reference=self.k)
  class Other(XorTestProvider):provider_id="OTHER"
  with self.assertRaisesRegex(EnrollmentError,"binding"):unprotect(Other(),x,associated_data=self.ad,key_reference=self.k)
 def test_associated_data_mutation_cannot_recover_original(self):
  x=protect(self.p,self.pt,associated_data=self.ad,key_reference=self.k)
  self.assertNotEqual(self.pt,unprotect(self.p,x,associated_data=self.ad+b"x",key_reference=self.k))
 def test_provider_id_required(self):
  class P:
   def protect(self,*a,**k):return b"x"
  with self.assertRaises(EnrollmentError):protect(P(),self.pt,associated_data=self.ad,key_reference=self.k)
 def test_contract_contains_no_secret_material_field(self):
  self.assertEqual({"provider_id","key_reference","protected_bytes"},set(ProtectedPayload.__dataclass_fields__))
