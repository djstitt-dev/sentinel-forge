import copy
from pathlib import Path
import tempfile
import unittest
from sentinel_forge.assembly import AssemblyContext, assemble_outbound
from sentinel_forge.courier import ConflictingReplay
from sentinel_forge.courier_effects import DurableEffectCoordinator, EffectStateError, ReconciliationRequired
from sentinel_forge.package import build_manifest
from sentinel_forge.transport import DisconnectedTransport, SimulatedTransport

class ExplodingTransport:
    def __init__(self): self.calls=0
    def effect(self,request):
        self.calls+=1
        raise RuntimeError("simulated crash after boundary")

class EffectCoordinatorTests(unittest.TestCase):
    def setUp(self):
        self.td=tempfile.TemporaryDirectory(); root=Path(self.td.name)
        (root/"x").write_bytes(b"x")
        m=build_manifest(root,["x"],work_package_revision="r1",artifact_type_class="candidate",classification_handling="controlled")
        c=AssemblyContext(work_package_id="wp",revision_id="r1",authorization_id="a1",authorizing_authority="operator",
          authorized_principal="forge",scope_reference="scope",target="scribe",operation="controlled-transfer",
          policy_reference="p1",classification_handling="controlled",correlation_id="c1",allowed_action_classes="transfer",
          intended_purpose_disposition="scribe-evaluation",expected_transfer_effect_class="controlled-copy",
          canonical_integrity_reference="ri1")
        self.objects=assemble_outbound(m,c).objects
        self.db=root/"effects.sqlite"
    def tearDown(self): self.td.cleanup()
    def coordinator(self): return DurableEffectCoordinator(self.db)

    def test_disconnected_transport_creates_known_rejection_not_transfer(self):
        c=self.coordinator(); out=c.execute(self.objects,DisconnectedTransport())
        self.assertEqual("REJECTED",out.state); self.assertEqual("REJECTED",c.state("c1").state)

    def test_simulated_transfer_records_ack_and_exact_replay_has_no_second_effect(self):
        c=self.coordinator(); t=SimulatedTransport("TRANSFERRED")
        first=c.execute(self.objects,t); second=self.coordinator().execute(self.objects,t)
        self.assertEqual("TRANSFERRED",first.state); self.assertEqual("TRANSFERRED",second.state)
        self.assertEqual("SIMULATED_ACK",second.acknowledgement); self.assertEqual(1,t.calls)

    def test_exception_after_boundary_becomes_sticky_unknown(self):
        c=self.coordinator(); t=ExplodingTransport()
        with self.assertRaises(ReconciliationRequired): c.execute(self.objects,t)
        self.assertEqual("OUTCOME_UNKNOWN",c.state("c1").state)
        with self.assertRaises(ReconciliationRequired): self.coordinator().execute(self.objects,t)
        self.assertEqual(1,t.calls)

    def test_partial_is_sticky_and_blocks_retry(self):
        c=self.coordinator(); t=SimulatedTransport("PARTIAL")
        self.assertEqual("PARTIAL",c.execute(self.objects,t).state)
        with self.assertRaises(ReconciliationRequired): self.coordinator().execute(self.objects,t)
        self.assertEqual(1,t.calls)

    def test_manual_reconciliation_allows_known_replay_without_new_effect(self):
        c=self.coordinator(); t=ExplodingTransport()
        with self.assertRaises(ReconciliationRequired): c.execute(self.objects,t)
        c.reconcile("c1",established_state="REJECTED")
        out=c.execute(self.objects,t)
        self.assertEqual("REJECTED",out.state); self.assertEqual(1,t.calls)

    def test_reconciliation_can_establish_transferred_with_ack(self):
        c=self.coordinator(); t=ExplodingTransport()
        with self.assertRaises(ReconciliationRequired): c.execute(self.objects,t)
        c.reconcile("c1",established_state="TRANSFERRED",acknowledgement="external-proof")
        out=c.execute(self.objects,t)
        self.assertEqual(("TRANSFERRED","external-proof"),(out.state,out.acknowledgement))
        self.assertEqual(1,t.calls)

    def test_cannot_reconcile_known_final_state(self):
        c=self.coordinator(); c.execute(self.objects,DisconnectedTransport())
        with self.assertRaises(EffectStateError): c.reconcile("c1",established_state="REJECTED")

    def test_conflicting_request_after_final_is_rejected(self):
        c=self.coordinator(); c.execute(self.objects,DisconnectedTransport())
        altered=copy.deepcopy(self.objects); altered["TransferRequest"]["intended_purpose_disposition"]="different"
        with self.assertRaises(ConflictingReplay): c.execute(altered,DisconnectedTransport())

    def test_no_transport_surface_exists_beyond_protocol_implementations(self):
        self.assertFalse(hasattr(self.coordinator(),"connect"))
        self.assertFalse(hasattr(self.coordinator(),"ssh"))

if __name__=="__main__": unittest.main()
