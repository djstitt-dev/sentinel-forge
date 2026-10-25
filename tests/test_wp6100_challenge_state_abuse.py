import json,tempfile,unittest
from pathlib import Path
from sentinel_forge.enrollment import EnrollmentError
from sentinel_forge.enrollment_session import ChallengeRegistry
class ChallengeStateAbuseTests(unittest.TestCase):
 def bad(self,value):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"c";p.write_text(json.dumps(value))
   with self.assertRaises(EnrollmentError):ChallengeRegistry(p)
 def test_root_array_rejected(self):self.bad([])
 def test_unknown_state_rejected(self):self.bad({"e":{"state":"MAGIC","challenge_id":"c","remote_identity":"r"}})
 def test_missing_field_rejected(self):self.bad({"e":{"state":"OUTSTANDING","challenge_id":"c"}})
 def test_extra_field_rejected(self):self.bad({"e":{"state":"OUTSTANDING","challenge_id":"c","remote_identity":"r","x":1}})
 def test_blank_challenge_rejected(self):self.bad({"e":{"state":"OUTSTANDING","challenge_id":"","remote_identity":"r"}})
 def test_blank_remote_rejected(self):self.bad({"e":{"state":"CONSUMED","challenge_id":"c","remote_identity":""}})
 def test_blank_enrollment_key_rejected(self):self.bad({"":{"state":"CONSUMED","challenge_id":"c","remote_identity":"r"}})
