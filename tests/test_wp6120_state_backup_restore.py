import dataclasses,tempfile,unittest
from pathlib import Path
from sentinel_forge.enrollment import EnrollmentError
from sentinel_forge.state_backup import ALLOWED,build_state_backup_manifest,verify_restored_state
class StateBackupRestoreTests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();r=Path(self.t.name);self.files={}
  for n in ALLOWED:p=r/n;p.write_bytes((n+"\n").encode());self.files[n]=p
  self.m=build_state_backup_manifest(relationship_id="rel",files=self.files)
 def tearDown(self):self.t.cleanup()
 def test_exact_restore_verifies(self):verify_restored_state(self.m,expected_relationship_id="rel",files=self.files)
 def test_wrong_relationship_rejected(self):
  with self.assertRaises(EnrollmentError):verify_restored_state(self.m,expected_relationship_id="other",files=self.files)
 def test_manifest_digest_tamper_rejected(self):
  with self.assertRaises(EnrollmentError):verify_restored_state(dataclasses.replace(self.m,manifest_digest="sha256:evil"),expected_relationship_id="rel",files=self.files)
 def test_missing_restore_file_rejected(self):
  x=dict(self.files);x.pop("queue")
  with self.assertRaises(EnrollmentError):verify_restored_state(self.m,expected_relationship_id="rel",files=x)
 def test_extra_restore_file_rejected(self):
  x=dict(self.files);x["secret"]=self.files["queue"]
  with self.assertRaises(EnrollmentError):verify_restored_state(self.m,expected_relationship_id="rel",files=x)
 def test_build_missing_state_rejected(self):
  x=dict(self.files);x.pop("evidence")
  with self.assertRaises(EnrollmentError):build_state_backup_manifest(relationship_id="rel",files=x)
 def test_build_extra_state_rejected(self):
  x=dict(self.files);x["private_key"]=self.files["queue"]
  with self.assertRaises(EnrollmentError):build_state_backup_manifest(relationship_id="rel",files=x)
def _mutation(name):
 def test(self):
  self.files[name].write_bytes(b"corrupt")
  with self.assertRaises(EnrollmentError):verify_restored_state(self.m,expected_relationship_id="rel",files=self.files)
 return test
for _n in ALLOWED:setattr(StateBackupRestoreTests,"test_corrupt_"+_n+"_rejected",_mutation(_n))
