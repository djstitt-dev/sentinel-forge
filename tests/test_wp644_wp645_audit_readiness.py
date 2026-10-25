import tempfile,unittest
from pathlib import Path
from sentinel_forge.courier_audit import record_courier_event
from sentinel_forge.evidence import EvidenceJournal
from sentinel_forge.enrollment import EnrollmentError
from sentinel_forge.transport_readiness import assess_transport_readiness,require_transport_ready

class AuditReadinessTests(unittest.TestCase):
 def test_courier_event_uses_required_evidence_context(self):
  with tempfile.TemporaryDirectory() as td:
   e=EvidenceJournal(Path(td)/"e.jsonl")
   x=record_courier_event(e,correlation_id="c",actor="forge",target="reaper",authorization_reference="a",
    input_identity="i",output_identity="o",outcome="QUEUED",reason="delivery")
   self.assertEqual("COURIER_TRANSPORT",x.source_context);self.assertEqual("COURIER_AUDIT",x.collector_method)
 def test_missing_audit_identity_fails(self):
  with tempfile.TemporaryDirectory() as td:
   with self.assertRaises(EnrollmentError):record_courier_event(EvidenceJournal(Path(td)/"e"),correlation_id="",actor="forge",target="r",authorization_reference="a",input_identity="i",output_identity="o",outcome="x",reason="x")
 def test_all_gates_ready(self):
  r=assess_transport_readiness(enrollment_state="ACTIVE",revoked=False,current_credential=True,current_session=True,
   unresolved_effect=False,unresolved_recovery=False,audit_available=True,assistant_independence_verified=True,
   protection_provider_approved=True,network_provider_approved=True)
  self.assertTrue(r.ready);self.assertEqual((),r.blockers);require_transport_ready(r)
 def test_current_reference_build_is_not_production_ready(self):
  r=assess_transport_readiness(enrollment_state="ACTIVE",revoked=False,current_credential=True,current_session=True,
   unresolved_effect=False,unresolved_recovery=False,audit_available=True,assistant_independence_verified=False,
   protection_provider_approved=False,network_provider_approved=False)
  self.assertFalse(r.ready)
  self.assertEqual(("ASSISTANT_INDEPENDENCE_UNVERIFIED","PROTECTION_PROVIDER_UNAPPROVED","NETWORK_PROVIDER_UNAPPROVED"),r.blockers)
  with self.assertRaisesRegex(EnrollmentError,"transport not ready"):require_transport_ready(r)
 def test_every_gate_blocks(self):
  r=assess_transport_readiness(enrollment_state="VERIFIED",revoked=True,current_credential=False,current_session=False,
   unresolved_effect=True,unresolved_recovery=True,audit_available=False,assistant_independence_verified=False,
   protection_provider_approved=False,network_provider_approved=False)
  self.assertEqual(10,len(r.blockers))
