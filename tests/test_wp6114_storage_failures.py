import hashlib,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from sentinel_forge.artifact_store import ArtifactStore
from sentinel_forge.courier_queue import CourierQueue
from sentinel_forge.evidence import EvidenceJournal
from sentinel_forge.enrollment import EnrollmentError
class StorageFailureTests(unittest.TestCase):
 def test_artifact_stage_fsync_failure_not_success(self):
  with tempfile.TemporaryDirectory() as td:
   s=ArtifactStore(Path(td));p=b"x";i="sha256:"+hashlib.sha256(p).hexdigest()
   with patch("sentinel_forge.artifact_store.os.fsync",side_effect=OSError("full")):
    with self.assertRaises(OSError):s.stage(p,expected_identity=i)
 def test_artifact_stage_replace_failure_not_success(self):
  with tempfile.TemporaryDirectory() as td:
   s=ArtifactStore(Path(td));p=b"x";i="sha256:"+hashlib.sha256(p).hexdigest()
   with patch("sentinel_forge.artifact_store.os.replace",side_effect=OSError("full")):
    with self.assertRaises(OSError):s.stage(p,expected_identity=i)
 def test_artifact_accept_replace_failure_preserves_staging(self):
  with tempfile.TemporaryDirectory() as td:
   s=ArtifactStore(Path(td));p=b"x";i="sha256:"+hashlib.sha256(p).hexdigest();s.stage(p,expected_identity=i)
   with patch("sentinel_forge.artifact_store.os.replace",side_effect=OSError("full")):
    with self.assertRaises(OSError):s.accept(i)
   self.assertTrue(s._path("staging",i).exists())
 def test_artifact_quarantine_replace_failure_preserves_staging(self):
  with tempfile.TemporaryDirectory() as td:
   s=ArtifactStore(Path(td));p=b"x";i="sha256:"+hashlib.sha256(p).hexdigest();s.stage(p,expected_identity=i)
   with patch("sentinel_forge.artifact_store.os.replace",side_effect=OSError("full")):
    with self.assertRaises(OSError):s.quarantine(i,reason="bad")
   self.assertTrue(s._path("staging",i).exists())
 def test_queue_directory_fsync_failure_not_success(self):
  with tempfile.TemporaryDirectory() as td:
   q=CourierQueue(Path(td)/"q")
   with patch("sentinel_forge.courier_queue.os.fsync",side_effect=OSError("full")):
    with self.assertRaises(OSError):q.enqueue(relationship_id="r",artifact_identity="a",operation="d",payload_identity="p")
 def test_evidence_fsync_failure_not_success(self):
  with tempfile.TemporaryDirectory() as td:
   e=EvidenceJournal(Path(td)/"e")
   with patch("sentinel_forge.evidence.os.fsync",side_effect=OSError("full")):
    with self.assertRaises(OSError):e.append(correlation_id="c")
 def test_evidence_write_failure_not_success(self):
  with tempfile.TemporaryDirectory() as td:
   e=EvidenceJournal(Path(td)/"e")
   with patch("sentinel_forge.evidence.private_open",side_effect=OSError("full")):
    with self.assertRaises(OSError):e.append(correlation_id="c")
 def test_evidence_prior_event_survives_next_write_failure(self):
  with tempfile.TemporaryDirectory() as td:
   e=EvidenceJournal(Path(td)/"e");e.append(correlation_id="one")
   with patch("sentinel_forge.evidence.os.fsync",side_effect=OSError("full")):
    with self.assertRaises(OSError):e.append(correlation_id="two")
   self.assertGreaterEqual(len(e.verify()),1)
