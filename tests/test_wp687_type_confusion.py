import json,tempfile,unittest
from pathlib import Path
from sentinel_forge.enrollment import EnrollmentError,build_bundle
from sentinel_forge.session import ReplayRegistry,derive_session
from sentinel_forge.trust_domain import derive_trust_domain
from sentinel_forge.courier_ack import build_ack
from sentinel_forge.transport_health import assess_transport_health

class TypeConfusionTests(unittest.TestCase):
 def domain(self):return derive_trust_domain(build_bundle(forge_identity="forge",remote_identity="reaper",remote_role="reaper",permitted_actions=["receive"],permitted_target="reaper",policy_reference="p"))
 def test_session_bool_generation_rejected(self):
  with self.assertRaises(EnrollmentError):derive_session(self.domain(),generation=True,challenge=b"R"*32)
 def test_replay_persisted_bool_generation_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"r";p.write_text(json.dumps({"rel":{"generation":True,"session_id":"s","highest":1}}))
   with self.assertRaises(EnrollmentError):ReplayRegistry(p).state("rel")
 def test_replay_persisted_bool_highest_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"r";p.write_text(json.dumps({"rel":{"generation":1,"session_id":"s","highest":False}}))
   with self.assertRaises(EnrollmentError):ReplayRegistry(p).state("rel")
 def test_replay_negative_persisted_values_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"r";p.write_text(json.dumps({"rel":{"generation":-1,"session_id":"s","highest":0}}))
   with self.assertRaises(EnrollmentError):ReplayRegistry(p).state("rel")
