import json,tempfile,unittest
from pathlib import Path
from sentinel_forge.enrollment import EnrollmentRegistry,EnrollmentError,build_bundle
class EnrollmentRegistryHardening(unittest.TestCase):
 def staged(self,td):
  p=Path(td)/"e";r=EnrollmentRegistry(p);b=build_bundle(forge_identity="f",remote_identity="r",remote_role="reaper",permitted_actions=["x"],permitted_target="r",policy_reference="p");r.stage(b);return p,b
 def test_unknown_state_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   p,b=self.staged(td);d=json.loads(p.read_text());d[b.enrollment_id]["state"]="MAGIC";p.write_text(json.dumps(d))
   with self.assertRaises(EnrollmentError):EnrollmentRegistry(p)
 def test_extra_field_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   p,b=self.staged(td);d=json.loads(p.read_text());d[b.enrollment_id]["x"]=1;p.write_text(json.dumps(d))
   with self.assertRaises(EnrollmentError):EnrollmentRegistry(p)
 def test_missing_field_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   p,b=self.staged(td);d=json.loads(p.read_text());del d[b.enrollment_id]["remote_identity"];p.write_text(json.dumps(d))
   with self.assertRaises(EnrollmentError):EnrollmentRegistry(p)
 def test_verified_requires_proof_digest(self):
  with tempfile.TemporaryDirectory() as td:
   p,b=self.staged(td);d=json.loads(p.read_text());d[b.enrollment_id]["state"]="VERIFIED";p.write_text(json.dumps(d))
   with self.assertRaises(EnrollmentError):EnrollmentRegistry(p)
 def test_blank_identity_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   p,b=self.staged(td);d=json.loads(p.read_text());d[b.enrollment_id]["remote_identity"]="";p.write_text(json.dumps(d))
   with self.assertRaises(EnrollmentError):EnrollmentRegistry(p)
