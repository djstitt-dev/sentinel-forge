import hashlib,tempfile,unittest
from pathlib import Path
from sentinel_forge.artifact_store import ArtifactStore
from sentinel_forge.enrollment import EnrollmentError

class ArtifactStoreTests(unittest.TestCase):
 def setUp(self):self.td=tempfile.TemporaryDirectory();self.s=ArtifactStore(Path(self.td.name));self.p=b"artifact";self.i="sha256:"+hashlib.sha256(self.p).hexdigest()
 def tearDown(self):self.td.cleanup()
 def test_stage_then_atomic_accept(self):
  self.s.stage(self.p,expected_identity=self.i);p=self.s.accept(self.i);self.assertEqual(self.p,p.read_bytes());self.assertFalse((Path(self.td.name)/"staging"/self.i[7:]).exists())
 def test_wrong_identity_never_stages(self):
  with self.assertRaisesRegex(EnrollmentError,"identity mismatch"):self.s.stage(self.p,expected_identity="sha256:"+"0"*64)
 def test_corrupted_stage_not_accepted(self):
  self.s.stage(self.p,expected_identity=self.i);(Path(self.td.name)/"staging"/self.i[7:]).write_bytes(b"evil")
  with self.assertRaisesRegex(EnrollmentError,"corrupted"):self.s.accept(self.i)
 def test_quarantine_preserves_payload_and_reason(self):
  self.s.stage(self.p,expected_identity=self.i);q=self.s.quarantine(self.i,reason="policy rejected")
  self.assertEqual(self.p,q.read_bytes());self.assertTrue(q.with_suffix(".reason.json").exists())
 def test_accept_is_idempotent_after_completed_move(self):
  self.s.stage(self.p,expected_identity=self.i);a=self.s.accept(self.i);self.assertEqual(a,self.s.accept(self.i))
