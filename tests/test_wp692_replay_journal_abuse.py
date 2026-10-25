import json,tempfile,unittest
from pathlib import Path
from sentinel_forge.delivery_journal import DeliveryJournal
from sentinel_forge.enrollment import EnrollmentError
from sentinel_forge.session import ReplayRegistry
class ReplayJournalAbuseTests(unittest.TestCase):
 def test_replay_root_nonobject_fails(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"r";p.write_text("[]")
   with self.assertRaises(EnrollmentError):ReplayRegistry(p).state("r")
 def test_replay_extra_field_fails(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"r";p.write_text(json.dumps({"r":{"generation":1,"session_id":"s","highest":1,"x":1}}))
   with self.assertRaises(EnrollmentError):ReplayRegistry(p).state("r")
 def test_replay_string_highest_fails(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"r";p.write_text(json.dumps({"r":{"generation":1,"session_id":"s","highest":"1"}}))
   with self.assertRaises(EnrollmentError):ReplayRegistry(p).state("r")
 def journal(self,td):
  p=Path(td)/"j";j=DeliveryJournal(p);j.append(item_id="i",relationship_id="r",delivery_sequence=None,prior_state=None,state="QUEUED",artifact_identity="a",reason="q");return p,j
 def mutate(self,field,value):
  with tempfile.TemporaryDirectory() as td:
   p,j=self.journal(td);r=json.loads(p.read_text());r[field]=value;p.write_text(json.dumps(r)+"\n")
   with self.assertRaises(EnrollmentError):j.verify()
 def test_journal_sequence_mutation(self):self.mutate("sequence",2)
 def test_journal_previous_hash_mutation(self):self.mutate("previous_hash","f"*64)
 def test_journal_event_hash_mutation(self):self.mutate("event_hash","f"*64)
 def test_journal_state_mutation(self):self.mutate("state","ACKNOWLEDGED")
 def test_journal_item_mutation(self):self.mutate("item_id","other")
 def test_journal_relationship_mutation(self):self.mutate("relationship_id","other")
 def test_journal_artifact_mutation(self):self.mutate("artifact_identity","evil")
