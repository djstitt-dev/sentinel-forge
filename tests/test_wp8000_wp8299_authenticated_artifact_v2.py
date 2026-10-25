import io,json,tarfile,tempfile,unittest
from pathlib import Path
from sentinel_forge.authenticity import TestOnlyHMACSigner,TestOnlyHMACVerifier
from sentinel_forge.enrollment import EnrollmentError,build_bundle
from sentinel_forge.enrollment_artifact_v2 import *
class ArtifactV2(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.p=Path(self.t.name)/"a.tar";self.b=build_bundle(forge_identity="forge",remote_identity="reaper",remote_role="reaper",permitted_actions=["receive"],permitted_target="reaper",policy_reference="p")
  self.s=TestOnlyHMACSigner("forge","test-key",b"k"*32);self.v=TestOnlyHMACVerifier({("forge","test-key"):b"k"*32});export_authenticated_artifact(self.b,self.p,signer=self.s)
 def tearDown(self):self.t.cleanup()
 def val(self,**kw):return validate_authenticated_artifact(self.p,verifier=self.v,expected_signer_identity=kw.get("signer","forge"),expected_key_reference=kw.get("key","test-key"),expected_remote_identity=kw.get("remote","reaper"))
 def rewrite(self,mut):
  with tarfile.open(self.p,"r") as tf:items=[(m,tf.extractfile(m).read()) for m in tf.getmembers()]
  with tarfile.open(self.p,"w") as tf:
   for m,raw in items:
    raw=mut(m.name,raw);m.size=len(raw);tf.addfile(m,io.BytesIO(raw))
 def test_valid(self):self.assertTrue(self.val()["validated"])
 def test_wrong_signer_key_remote_matrix(self):
  for kw in ({"signer":"other"},{"key":"other"},{"remote":"other"}):
   with self.subTest(kw=kw):
    with self.assertRaises(EnrollmentError):self.val(**kw)
 def test_every_member_byte_mutation_rejected(self):
  with tarfile.open(self.p,"r") as tf:base={m.name:tf.extractfile(m).read() for m in tf.getmembers()}
  for name,raw in base.items():
   for i in range(min(len(raw),64)):
    with self.subTest(name=name,i=i):
     export_authenticated_artifact(self.b,self.p,signer=self.s)
     def mut(n,b,name=name,i=i):
      if n!=name:return b
      x=bytearray(b);x[i]^=1;return bytes(x)
     self.rewrite(mut)
     with self.assertRaises(EnrollmentError):self.val()
 def test_extra_missing_reordered_members_rejected(self):
  with tarfile.open(self.p,"r") as tf:items=[(m,tf.extractfile(m).read()) for m in tf.getmembers()]
  variants=(items[:-1],items[::-1],items+[items[-1]])
  for rows in variants:
   with self.subTest(n=len(rows)):
    with tarfile.open(self.p,"w") as tf:
     for m,raw in rows:tf.addfile(m,io.BytesIO(raw))
    with self.assertRaises(EnrollmentError):self.val()
    export_authenticated_artifact(self.b,self.p,signer=self.s)
 def test_symlink_outer_rejected(self):
  link=Path(self.t.name)/"link";link.symlink_to(self.p)
  with self.assertRaises(EnrollmentError):validate_authenticated_artifact(link,verifier=self.v,expected_signer_identity="forge",expected_key_reference="test-key")
