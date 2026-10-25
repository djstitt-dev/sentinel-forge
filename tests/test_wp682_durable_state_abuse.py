import json,tempfile,unittest
from pathlib import Path
from sentinel_forge.courier_queue import CourierQueue
from sentinel_forge.delivery_journal import DeliveryJournal
from sentinel_forge.enrollment import EnrollmentError
from sentinel_forge.send_sequence import SendSequenceRegistry

class DurableStateAbuseTests(unittest.TestCase):
 def queue(self,td):
  p=Path(td)/"q";q=CourierQueue(p);i=q.enqueue(relationship_id="r",artifact_identity="a",operation="d",payload_identity="p");return p,q,i
 def test_queue_truncated_json_fails(self):
  with tempfile.TemporaryDirectory() as td:
   p,q,i=self.queue(td);p.write_text('{"bad"')
   with self.assertRaises(EnrollmentError):CourierQueue(p)
 def test_queue_wrong_sequence_type_fails(self):
  with tempfile.TemporaryDirectory() as td:
   p,q,i=self.queue(td);db=json.loads(p.read_text());db[i]["state"]="PREPARED";db[i]["sequence"]="1";p.write_text(json.dumps(db))
   with self.assertRaises(EnrollmentError):CourierQueue(p)
 def test_queue_ack_on_nonack_state_fails(self):
  with tempfile.TemporaryDirectory() as td:
   p,q,i=self.queue(td);db=json.loads(p.read_text());db[i]["acknowledgement"]="forged";p.write_text(json.dumps(db))
   with self.assertRaises(EnrollmentError):CourierQueue(p)
 def test_journal_truncation_fails(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"j";j=DeliveryJournal(p);j.append(item_id="i",relationship_id="r",delivery_sequence=None,prior_state=None,state="QUEUED",artifact_identity="a",reason="q");p.write_bytes(p.read_bytes()[:-5])
   with self.assertRaises(EnrollmentError):j.verify()
 def test_journal_duplicate_line_fails(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"j";j=DeliveryJournal(p);j.append(item_id="i",relationship_id="r",delivery_sequence=None,prior_state=None,state="QUEUED",artifact_identity="a",reason="q");raw=p.read_bytes();p.write_bytes(raw+raw)
   with self.assertRaises(EnrollmentError):j.verify()
 def test_send_sequence_extra_field_fails(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"s";SendSequenceRegistry(p);p.write_text(json.dumps({"r":{"generation":1,"session_id":"s","highest":1,"evil":1}}))
   with self.assertRaises(EnrollmentError):SendSequenceRegistry(p)
 def test_send_sequence_bool_generation_fails(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"s";SendSequenceRegistry(p);p.write_text(json.dumps({"r":{"generation":True,"session_id":"s","highest":1}}))
   with self.assertRaises(EnrollmentError):SendSequenceRegistry(p)
