import json,tempfile,unittest
from pathlib import Path
from sentinel_forge.credential_reference import build_credential_reference
from sentinel_forge.credential_registry import CredentialReferenceRegistry
from sentinel_forge.enrollment import EnrollmentError,build_bundle
from sentinel_forge.recovery_intent import RecoveryIntentLedger
from sentinel_forge.trust_domain import derive_trust_domain
class RegistryIntegrityTests(unittest.TestCase):
 def domain(self,n):return derive_trust_domain(build_bundle(forge_identity="forge",remote_identity=n,remote_role=n,permitted_actions=["receive"],permitted_target=n,policy_reference="p"))
 def test_credential_relationship_key_mismatch(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"c";d=self.domain("r");x=CredentialReferenceRegistry(p);x.register_initial(d,build_credential_reference(d,generation=1,key_reference="k"));db=json.loads(p.read_text());db["relationships"]["evil"]=db["relationships"].pop(d.relationship_id);p.write_text(json.dumps(db))
   with self.assertRaises(EnrollmentError):CredentialReferenceRegistry(p)
 def test_credential_duplicate_key_reference_detected_on_reload(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"c";a=self.domain("a");b=self.domain("b");x=CredentialReferenceRegistry(p);x.register_initial(a,build_credential_reference(a,generation=1,key_reference="ka"));x.register_initial(b,build_credential_reference(b,generation=1,key_reference="kb"));db=json.loads(p.read_text());db["relationships"][b.relationship_id]["key_reference"]="ka";p.write_text(json.dumps(db))
   with self.assertRaises(EnrollmentError):CredentialReferenceRegistry(p)
 def test_credential_unknown_top_field(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"c";CredentialReferenceRegistry(p);db=json.loads(p.read_text());db["evil"]=1;p.write_text(json.dumps(db))
   with self.assertRaises(EnrollmentError):CredentialReferenceRegistry(p)
 def test_recovery_intent_digest_tamper(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"r";x=RecoveryIntentLedger(p);x.prepare(plan_digest="p",target="t",observation_digest="o");db=json.loads(p.read_text());db["p"]["target"]="evil";p.write_text(json.dumps(db))
   with self.assertRaises(EnrollmentError):RecoveryIntentLedger(p)
 def test_recovery_intent_id_tamper(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"r";x=RecoveryIntentLedger(p);x.prepare(plan_digest="p",target="t",observation_digest="o");db=json.loads(p.read_text());db["p"]["intent_id"]="recovery-intent:evil";p.write_text(json.dumps(db))
   with self.assertRaises(EnrollmentError):RecoveryIntentLedger(p)
 def test_recovery_intent_key_mismatch(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"r";x=RecoveryIntentLedger(p);x.prepare(plan_digest="p",target="t",observation_digest="o");db=json.loads(p.read_text());db["other"]=db.pop("p");p.write_text(json.dumps(db))
   with self.assertRaises(EnrollmentError):RecoveryIntentLedger(p)
