import hashlib,tempfile,unittest
from pathlib import Path
from sentinel_forge.artifact_store import ArtifactStore,MAX_ARTIFACT
from sentinel_forge.enrollment import EnrollmentError
class ArtifactAbuseTests(unittest.TestCase):
 def test_empty_payload_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   with self.assertRaises(EnrollmentError):ArtifactStore(Path(td)).stage(b"",expected_identity="sha256:"+"0"*64)
 def test_oversized_payload_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   p=b"x"*(MAX_ARTIFACT+1);i="sha256:"+hashlib.sha256(p).hexdigest()
   with self.assertRaises(EnrollmentError):ArtifactStore(Path(td)).stage(p,expected_identity=i)
 def test_invalid_identity_format_rejected_on_accept(self):
  with tempfile.TemporaryDirectory() as td:
   with self.assertRaises(EnrollmentError):ArtifactStore(Path(td)).accept("../evil")
 def test_quarantine_requires_reason(self):
  with tempfile.TemporaryDirectory() as td:
   s=ArtifactStore(Path(td));p=b"x";i="sha256:"+hashlib.sha256(p).hexdigest();s.stage(p,expected_identity=i)
   with self.assertRaises(EnrollmentError):s.quarantine(i,reason="")
 def test_accepted_corruption_detected_on_idempotent_accept(self):
  with tempfile.TemporaryDirectory() as td:
   s=ArtifactStore(Path(td));p=b"x";i="sha256:"+hashlib.sha256(p).hexdigest();a=s.accept(i) if False else None;s.stage(p,expected_identity=i);a=s.accept(i);a.write_bytes(b"evil")
   with self.assertRaises(EnrollmentError):s.accept(i)
