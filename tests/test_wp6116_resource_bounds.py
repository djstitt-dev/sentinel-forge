import hashlib,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from sentinel_forge.artifact_store import ArtifactStore
from sentinel_forge.courier_queue import CourierQueue
from sentinel_forge.enrollment import EnrollmentError
class ResourceBoundsTests(unittest.TestCase):
 def art(self,s,p=b"x"):i="sha256:"+hashlib.sha256(p).hexdigest();s.stage(p,expected_identity=i);return i
 def test_both_staging_and_accepted_is_ambiguous(self):
  with tempfile.TemporaryDirectory() as td:
   s=ArtifactStore(Path(td));i=self.art(s);dst=s._path("accepted",i);dst.write_bytes(b"x")
   with self.assertRaises(EnrollmentError):s.accept(i)
 def test_corrupt_staging_blocks_accept(self):
  with tempfile.TemporaryDirectory() as td:
   s=ArtifactStore(Path(td));i=self.art(s);s._path("staging",i).write_bytes(b"evil")
   with self.assertRaises(EnrollmentError):s.accept(i)
 def test_corrupt_staging_blocks_quarantine(self):
  with tempfile.TemporaryDirectory() as td:
   s=ArtifactStore(Path(td));i=self.art(s);s._path("staging",i).write_bytes(b"evil")
   with self.assertRaises(EnrollmentError):s.quarantine(i,reason="bad")
 def test_missing_staging_blocks_accept(self):
  with tempfile.TemporaryDirectory() as td:
   s=ArtifactStore(Path(td))
   with self.assertRaises(EnrollmentError):s.accept("sha256:"+"0"*64)
 def test_missing_staging_blocks_quarantine(self):
  with tempfile.TemporaryDirectory() as td:
   s=ArtifactStore(Path(td))
   with self.assertRaises(EnrollmentError):s.quarantine("sha256:"+"0"*64,reason="bad")
 def test_queue_capacity_counts_active(self):
  with tempfile.TemporaryDirectory() as td:
   q=CourierQueue(Path(td)/"q")
   with patch("sentinel_forge.courier_queue.MAX_ITEMS",2):
    q.enqueue(relationship_id="r",artifact_identity="a1",operation="d",payload_identity="p1");q.enqueue(relationship_id="r",artifact_identity="a2",operation="d",payload_identity="p2")
    with self.assertRaises(EnrollmentError):q.enqueue(relationship_id="r",artifact_identity="a3",operation="d",payload_identity="p3")
 def test_terminal_item_releases_capacity(self):
  with tempfile.TemporaryDirectory() as td:
   q=CourierQueue(Path(td)/"q")
   with patch("sentinel_forge.courier_queue.MAX_ITEMS",1):
    i=q.enqueue(relationship_id="r",artifact_identity="a1",operation="d",payload_identity="p1");q.transition(i,expected="QUEUED",new="CANCELLED");q.enqueue(relationship_id="r",artifact_identity="a2",operation="d",payload_identity="p2")
 def test_exact_duplicate_does_not_consume_capacity(self):
  with tempfile.TemporaryDirectory() as td:
   q=CourierQueue(Path(td)/"q")
   with patch("sentinel_forge.courier_queue.MAX_ITEMS",1):
    a=q.enqueue(relationship_id="r",artifact_identity="a",operation="d",payload_identity="p");b=q.enqueue(relationship_id="r",artifact_identity="a",operation="d",payload_identity="p");self.assertEqual(a,b)
 def test_invalid_artifact_identity_path_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   with self.assertRaises(EnrollmentError):ArtifactStore(Path(td)).accept("sha256:../evil")
 def test_short_artifact_identity_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   with self.assertRaises(EnrollmentError):ArtifactStore(Path(td)).accept("sha256:abc")
 def test_nonstring_artifact_identity_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   with self.assertRaises(EnrollmentError):ArtifactStore(Path(td)).accept(None)
