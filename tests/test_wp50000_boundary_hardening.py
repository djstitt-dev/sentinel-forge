import dataclasses,tempfile,unittest
from pathlib import Path
from sentinel_forge.assistant_independence import *
from sentinel_forge.authenticity import *
from sentinel_forge.enrollment import EnrollmentError
from sentinel_forge.recovery import *
from sentinel_forge.state_backup import *
class BoundaryHardening(unittest.TestCase):
 def test_authenticity_wrong_types_fail_closed(self):
  s=TestOnlyHMACSigner("forge","k",b"k");v=TestOnlyHMACVerifier({("forge","k"):b"k"});e=create_envelope(b"x",s)
  for bad in (dataclasses.replace(e,signature=None),dataclasses.replace(e,algorithm=[]),dataclasses.replace(e,subject_digest=1)):
   self.assertFalse(verify_envelope(b"x",bad,v,expected_signer_identity="forge",expected_key_reference="k"))
  self.assertFalse(verify_envelope("x",e,v,expected_signer_identity="forge",expected_key_reference="k"))
 def test_bad_signer_metadata_rejected(self):
  class S:
   signer_identity=[];algorithm="a";key_reference="k"
   def sign(self,x):return b"x"
  with self.assertRaises(AuthenticityError):create_envelope(b"x",S())
 def test_recovery_type_confusion_becomes_operator_required(self):
  o=RecoveryObservation([], "t","i","d")
  self.assertEqual(OPERATOR_REQUIRED,classify(o))
 def test_backup_symlink_source_and_restore_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   r=Path(td);files={}
   for n in ALLOWED:p=r/n;p.write_bytes(n.encode());files[n]=p
   target=files["queue"];link=r/"link";link.symlink_to(target);x=dict(files);x["queue"]=link
   with self.assertRaises(EnrollmentError):build_state_backup_manifest(relationship_id="r",files=x)
   m=build_state_backup_manifest(relationship_id="r",files=files)
   with self.assertRaises(EnrollmentError):verify_restored_state(m,expected_relationship_id="r",files=x)
 def test_independence_malformed_finding_rejected(self):
  with self.assertRaises(EnrollmentError):build_inventory(forge_identity="f",collector_method="c",categories_observed=list(REQUIRED_CATEGORIES),findings=[{}])
  f=InventoryFinding("processes","x","i","false","e")
  with self.assertRaises(EnrollmentError):build_inventory(forge_identity="f",collector_method="c",categories_observed=list(REQUIRED_CATEGORIES),findings=[f])
