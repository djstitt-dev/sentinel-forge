import dataclasses,tempfile,unittest
from pathlib import Path
from sentinel_forge.enrollment import EnrollmentError
from sentinel_forge.state_backup import ALLOWED,build_state_backup_manifest,verify_restored_state
class BackupManifestMutationTests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();r=Path(self.t.name);self.f={}
  for n in ALLOWED:p=r/n;p.write_text(n);self.f[n]=p
  self.m=build_state_backup_manifest(relationship_id="rel",files=self.f)
 def tearDown(self):self.t.cleanup()
 def badrows(self,rows):
  m=dataclasses.replace(self.m,files=tuple(rows))
  with self.assertRaises(EnrollmentError):verify_restored_state(m,expected_relationship_id="rel",files=self.f)
 def test_remove_queue_row(self):self.badrows([x for x in self.m.files if x[0]!="queue"])
 def test_remove_journal_row(self):self.badrows([x for x in self.m.files if x[0]!="delivery_journal"])
 def test_remove_evidence_row(self):self.badrows([x for x in self.m.files if x[0]!="evidence"])
 def test_remove_credential_reference_row(self):self.badrows([x for x in self.m.files if x[0]!="credential_references"])
 def test_duplicate_row(self):self.badrows(list(self.m.files)+[self.m.files[0]])
 def test_row_digest_mutation(self):
  rows=list(self.m.files);n,d,z=rows[0];rows[0]=(n,"sha256:evil",z);self.badrows(rows)
 def test_row_size_mutation(self):
  rows=list(self.m.files);n,d,z=rows[0];rows[0]=(n,d,z+1);self.badrows(rows)
 def test_row_name_mutation(self):
  rows=list(self.m.files);n,d,z=rows[0];rows[0]=("private_key",d,z);self.badrows(rows)
 def test_format_mutation(self):
  with self.assertRaises(EnrollmentError):verify_restored_state(dataclasses.replace(self.m,format="evil"),expected_relationship_id="rel",files=self.f)
 def test_relationship_mutation(self):
  with self.assertRaises(EnrollmentError):verify_restored_state(dataclasses.replace(self.m,relationship_id="evil"),expected_relationship_id="rel",files=self.f)
 def test_blank_relationship_build_rejected(self):
  with self.assertRaises(EnrollmentError):build_state_backup_manifest(relationship_id="",files=self.f)
 def test_unreadable_missing_source_rejected(self):
  self.f["queue"].unlink()
  with self.assertRaises(EnrollmentError):build_state_backup_manifest(relationship_id="rel",files=self.f)
 def test_zero_length_state_is_bound(self):
  self.f["queue"].write_bytes(b"");m=build_state_backup_manifest(relationship_id="rel",files=self.f);verify_restored_state(m,expected_relationship_id="rel",files=self.f)
 def test_same_bytes_deterministic_manifest(self):self.assertEqual(self.m,build_state_backup_manifest(relationship_id="rel",files=self.f))
