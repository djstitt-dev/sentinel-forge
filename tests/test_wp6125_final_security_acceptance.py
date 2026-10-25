import tempfile,unittest
from pathlib import Path
import sentinel_forge.api as api
from sentinel_forge.acceptance_runner import REQUIRED_OFFLINE,build_report
from sentinel_forge.evidence import EvidenceJournal
from sentinel_forge.evidence_anchor import build_evidence_head,verify_against_head
from sentinel_forge.state_backup import ALLOWED,build_state_backup_manifest,verify_restored_state
PROD=("framing_complete","protection_provider_complete","production_protection_approved","production_network_approved","assistant_independence_verified")
class FinalSecurityAcceptance(unittest.TestCase):
 def acceptance(self,**kw):
  x=dict(checks={n:True for n in REQUIRED_OFFLINE},framing_complete=True,protection_provider_complete=True,production_protection_approved=True,production_network_approved=True,assistant_independence_verified=True);x.update(kw);return build_report(**x)
 def test_all_explicit_acceptance_facts_can_be_green(self):self.assertTrue(self.acceptance().production_ready)
 def test_default_never_claims_production(self):self.assertFalse(build_report(checks={n:True for n in REQUIRED_OFFLINE}).production_ready)
 def test_1000_current_forge_remains_fail_closed_until_real_prerequisites_exist(self):
  r=build_report(checks={n:True for n in REQUIRED_OFFLINE})
  self.assertTrue(r.offline_invariants_passed);self.assertFalse(r.production_ready)
  self.assertEqual({"WP6.36_FRAMING_INCOMPLETE","WP6.37_PROTECTION_PROVIDER_INCOMPLETE","PRODUCTION_PROTECTION_UNAPPROVED","PRODUCTION_NETWORK_UNAPPROVED","ASSISTANT_INDEPENDENCE_UNVERIFIED"},set(r.blockers))
 def test_raw_authority_stores_not_safe_api(self):
  for n in ("CourierQueue","ReplayRegistry","TransitionIntentLedger","RecoveryIntentLedger","RevocationRegistry"):self.assertFalse(hasattr(api,n))
 def test_test_crypto_not_safe_api(self):self.assertFalse(any("HMAC" in n or "TestOnly" in n for n in dir(api)))
 def test_evidence_checkpoint_and_backup_compose(self):
  with tempfile.TemporaryDirectory() as td:
   r=Path(td);e=EvidenceJournal(r/"e");e.append(correlation_id="c");h=build_evidence_head(e,journal_identity="forge");verify_against_head(e,h)
   files={};
   for n in ALLOWED:
    p=r/("b-"+n);p.write_bytes(e.path.read_bytes() if n=="evidence" else n.encode());files[n]=p
   m=build_state_backup_manifest(relationship_id="rel",files=files);verify_restored_state(m,expected_relationship_id="rel",files=files)
 def test_evidence_checkpoint_detects_backup_evidence_rollback(self):
  with tempfile.TemporaryDirectory() as td:
   e=EvidenceJournal(Path(td)/"e");e.append(correlation_id="1");e.append(correlation_id="2");h=build_evidence_head(e,journal_identity="forge");e.path.write_text(e.path.read_text().splitlines()[0]+"\n")
   from sentinel_forge.evidence import EvidenceError
   with self.assertRaises(EvidenceError):verify_against_head(e,h)
def _inv(name):
 def t(self):
  checks={n:True for n in REQUIRED_OFFLINE};checks[name]=False;r=self.acceptance(checks=checks);self.assertFalse(r.offline_invariants_passed);self.assertFalse(r.production_ready);self.assertIn("OFFLINE_INVARIANT_FAILED:"+name,r.blockers)
 return t
for _n in REQUIRED_OFFLINE:setattr(FinalSecurityAcceptance,"test_invariant_"+_n.lower(),_inv(_n))
def _prod(name):
 def t(self):
  r=self.acceptance(**{name:False});self.assertFalse(r.production_ready)
 return t
for _n in PROD:setattr(FinalSecurityAcceptance,"test_production_gate_"+_n,_prod(_n))
