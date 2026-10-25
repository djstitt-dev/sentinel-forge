import json,tempfile,unittest
from pathlib import Path
from sentinel_forge.enrollment import EnrollmentError
from sentinel_forge.revocation import RevocationRegistry,make_revocation
from sentinel_forge.transition_intent import TransitionIntentLedger
from sentinel_forge.recovery_intent import RecoveryIntentLedger
class AuthorityStoreAbuseTests(unittest.TestCase):
 def test_revocation_digest_tamper_fails_reload(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"r";rr=RevocationRegistry(p);x=make_revocation(enrollment_id="e",remote_identity="r",operator_authorization_reference="a",reason="x",prior_state="ACTIVE");rr.revoke(x);db=json.loads(p.read_text());db["e"]["reason"]="evil";p.write_text(json.dumps(db))
   with self.assertRaises(EnrollmentError):RevocationRegistry(p)
 def test_revocation_key_identity_mismatch_fails(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"r";rr=RevocationRegistry(p);x=make_revocation(enrollment_id="e",remote_identity="r",operator_authorization_reference="a",reason="x",prior_state="ACTIVE");rr.revoke(x);db=json.loads(p.read_text());db["other"]=db.pop("e");p.write_text(json.dumps(db))
   with self.assertRaises(EnrollmentError):RevocationRegistry(p)
 def test_revocation_extra_field_fails(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"r";rr=RevocationRegistry(p);x=make_revocation(enrollment_id="e",remote_identity="r",operator_authorization_reference="a",reason="x",prior_state="ACTIVE");rr.revoke(x);db=json.loads(p.read_text());db["e"]["x"]=1;p.write_text(json.dumps(db))
   with self.assertRaises(EnrollmentError):RevocationRegistry(p)
 def intent(self,td):
  p=Path(td)/"i";l=TransitionIntentLedger(p);iid=l.prepare(enrollment_id="e",remote_identity="r",from_state="STAGED",to_state="VERIFIED",authorization_reference="a",reason="x");return p,l,iid
 def test_intent_digest_tamper_fails(self):
  with tempfile.TemporaryDirectory() as td:
   p,l,i=self.intent(td);db=json.loads(p.read_text());db["e"]["reason"]="evil";p.write_text(json.dumps(db))
   with self.assertRaises(EnrollmentError):TransitionIntentLedger(p)
 def test_intent_unknown_status_fails(self):
  with tempfile.TemporaryDirectory() as td:
   p,l,i=self.intent(td);db=json.loads(p.read_text());db["e"]["status"]="MAGIC";p.write_text(json.dumps(db))
   with self.assertRaises(EnrollmentError):TransitionIntentLedger(p)
 def test_intent_extra_field_fails(self):
  with tempfile.TemporaryDirectory() as td:
   p,l,i=self.intent(td);db=json.loads(p.read_text());db["e"]["evil"]=1;p.write_text(json.dumps(db))
   with self.assertRaises(EnrollmentError):TransitionIntentLedger(p)
 def test_intent_enrollment_key_mismatch_fails(self):
  with tempfile.TemporaryDirectory() as td:
   p,l,i=self.intent(td);db=json.loads(p.read_text());db["other"]=db.pop("e");p.write_text(json.dumps(db))
   with self.assertRaises(EnrollmentError):TransitionIntentLedger(p)
 def test_recovery_intent_unknown_status_fails(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"r";l=RecoveryIntentLedger(p);l.prepare(plan_digest="p",target="t",observation_digest="o");db=json.loads(p.read_text());db["p"]["status"]="MAGIC";p.write_text(json.dumps(db))
   with self.assertRaises(EnrollmentError):RecoveryIntentLedger(p)
