import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from sentinel_forge.courier_queue import CourierQueue
from sentinel_forge.delivery_journal import DeliveryJournal

class DurableFailureTests(unittest.TestCase):
 def test_queue_replace_failure_does_not_claim_transition(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"q";q=CourierQueue(p);i=q.enqueue(relationship_id="r",artifact_identity="a",operation="d",payload_identity="p")
   with patch("sentinel_forge.courier_queue.os.replace",side_effect=OSError("disk failure")):
    with self.assertRaises(OSError):q.transition(i,expected="QUEUED",new="PREPARED",sequence=1)
   self.assertEqual("QUEUED",CourierQueue(p).get(i)["state"])
 def test_queue_fsync_failure_is_not_success(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"q";q=CourierQueue(p);i=q.enqueue(relationship_id="r",artifact_identity="a",operation="d",payload_identity="p")
   with patch("sentinel_forge.courier_queue.os.fsync",side_effect=OSError("fsync failure")):
    with self.assertRaises(OSError):q.transition(i,expected="QUEUED",new="PREPARED",sequence=1)
 def test_journal_file_fsync_failure_is_not_success(self):
  with tempfile.TemporaryDirectory() as td:
   j=DeliveryJournal(Path(td)/"j")
   with patch("sentinel_forge.delivery_journal.os.fsync",side_effect=OSError("fsync failure")):
    with self.assertRaises(OSError):j.append(item_id="i",relationship_id="r",delivery_sequence=None,prior_state=None,state="QUEUED",artifact_identity="a",reason="q")
 def test_journal_write_failure_leaves_no_valid_event(self):
  with tempfile.TemporaryDirectory() as td:
   j=DeliveryJournal(Path(td)/"j")
   with patch("sentinel_forge.delivery_journal.private_open",side_effect=OSError("write failure")):
    with self.assertRaises(OSError):j.append(item_id="i",relationship_id="r",delivery_sequence=None,prior_state=None,state="QUEUED",artifact_identity="a",reason="q")
   self.assertEqual([],j.verify())
